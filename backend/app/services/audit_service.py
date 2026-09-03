import json
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from repackai.backend.app.models.domain import AuditLog

class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        old_val_str = json.dumps(old_value) if old_value else None
        new_val_str = json.dumps(new_value) if new_value else None
        
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value_json=old_val_str,
            new_value_json=new_val_str,
            ip_address=ip_address
        )
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
