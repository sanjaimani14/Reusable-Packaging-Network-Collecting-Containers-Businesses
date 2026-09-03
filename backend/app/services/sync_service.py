import json
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from repackai.backend.app.models.domain import SyncQueue, Container, Inspection

class SyncService:
    @staticmethod
    def queue_item(
        db: Session,
        entity_type: str,
        entity_id: str,
        payload: Dict[str, Any]
    ) -> SyncQueue:
        queue_entry = SyncQueue(
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=json.dumps(payload),
            status="PENDING"
        )
        db.add(queue_entry)
        db.commit()
        db.refresh(queue_entry)
        return queue_entry

    @staticmethod
    def get_pending_items(db: Session) -> List[SyncQueue]:
        return db.query(SyncQueue).filter(SyncQueue.status == "PENDING").all()

    @staticmethod
    def sync_pending_queue(db: Session) -> Dict[str, Any]:
        pending_items = SyncService.get_pending_items(db)
        synced_count = 0
        failed_count = 0
        errors = []
        
        for item in pending_items:
            try:
                # Simulating a sync action by loading the payload and updating status
                # In real life this would send a POST request to a remote server.
                # Here, we update the local model's status to synced
                payload = json.loads(item.payload_json)
                
                if item.entity_type == "Container":
                    container = db.query(Container).filter(Container.id == item.entity_id).first()
                    if container:
                        container.status = "synced"
                elif item.entity_type == "Inspection":
                    # We look up by container_id or inspection id
                    inspection = db.query(Inspection).filter(Inspection.id == int(item.entity_id)).first()
                    if inspection:
                        # Inspect data could be updated or synced
                        pass
                
                item.status = "SYNCED"
                synced_count += 1
            except Exception as e:
                item.retry_count += 1
                item.error_message = str(e)
                if item.retry_count >= 3:
                    item.status = "FAILED"
                failed_count += 1
                errors.append(f"Failed to sync {item.entity_type} {item.entity_id}: {str(e)}")
                
        db.commit()
        
        return {
            "synced_count": synced_count,
            "failed_count": failed_count,
            "errors": errors
        }
