import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from repackai.backend.app.models.domain import SyncQueue, Container, Inspection

class OfflineCacheManager:
    """
    Manages offline inspection/container caching and store-and-forward synchronization.
    Prevents duplicate submissions, manages retry counts, and transitions status
    from OFFLINE_PENDING to SYNCED or FAILED.
    """
    
    _network_online: bool = True  # Simulated network state toggle for testing
    
    @classmethod
    def set_network_state(cls, online: bool):
        cls._network_online = online
        
    @classmethod
    def is_network_online(cls) -> bool:
        return cls._network_online

    @classmethod
    def enqueue(
        cls,
        db: Session,
        entity_type: str,
        entity_id: str,
        payload: Dict[str, Any]
    ) -> SyncQueue:
        """
        Stores an item in the offline store-and-forward queue.
        Idempotent: if item already queued with PENDING status, updates payload without duplicating.
        """
        existing = db.query(SyncQueue).filter(
            SyncQueue.entity_type == entity_type,
            SyncQueue.entity_id == entity_id,
            SyncQueue.status == "PENDING"
        ).first()
        
        if existing:
            existing.payload_json = json.dumps(payload)
            existing.retry_count = 0
            existing.error_message = None
            db.commit()
            db.refresh(existing)
            return existing
            
        queue_item = SyncQueue(
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=json.dumps(payload),
            status="PENDING",
            retry_count=0
        )
        db.add(queue_item)
        db.commit()
        db.refresh(queue_item)
        return queue_item

    @classmethod
    def get_pending_items(cls, db: Session) -> List[SyncQueue]:
        return db.query(SyncQueue).filter(SyncQueue.status == "PENDING").all()

    @classmethod
    def sync_all(cls, db: Session, force: bool = False) -> Dict[str, Any]:
        """
        Synchronizes all pending items from store-and-forward queue.
        If network is offline and not forced, safely skips and returns OFFLINE_PENDING status.
        Handles duplicates, retries, and errors.
        """
        if not cls._network_online and not force:
            return {
                "status": "OFFLINE_PENDING",
                "synced_count": 0,
                "failed_count": 0,
                "pending_count": len(cls.get_pending_items(db)),
                "message": "Network offline; queue held safely in local persistence."
            }
            
        pending = cls.get_pending_items(db)
        synced_count = 0
        failed_count = 0
        errors = []
        
        for item in pending:
            try:
                payload = json.loads(item.payload_json)
                
                if item.entity_type == "Container":
                    container = db.query(Container).filter(Container.id == item.entity_id).first()
                    if container:
                        container.status = "synced"
                    else:
                        # Insert container if missing
                        new_c = Container(
                            id=item.entity_id,
                            container_type=payload.get("container_type", "Box"),
                            material=payload.get("material", "Cardboard"),
                            weight_kg=payload.get("weight_kg", 5.0),
                            age_months=payload.get("age_months", 1),
                            usage_count=payload.get("usage_count", 1),
                            recyclable=payload.get("recyclable", True),
                            status="synced"
                        )
                        db.add(new_c)
                        
                elif item.entity_type == "Inspection":
                    try:
                        insp_id = int(item.entity_id)
                        insp = db.query(Inspection).filter(Inspection.id == insp_id).first()
                        if insp:
                            insp.network_available = True
                    except ValueError:
                        pass
                        
                item.status = "SYNCED"
                item.error_message = None
                synced_count += 1
            except Exception as exc:
                item.retry_count += 1
                item.error_message = str(exc)
                if item.retry_count >= 3:
                    item.status = "FAILED"
                failed_count += 1
                errors.append(f"Sync error on {item.entity_type} {item.entity_id}: {str(exc)}")
                
        db.commit()
        return {
            "status": "SYNC_COMPLETE",
            "synced_count": synced_count,
            "failed_count": failed_count,
            "pending_count": len(cls.get_pending_items(db)),
            "errors": errors
        }
