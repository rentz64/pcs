from sqlalchemy.orm import Session
from .models import AuditLog


def audit(db: Session, user_id: int | None, action: str, entity_type: str, entity_id: str | None = None, details: str | None = None) -> None:
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details))
    db.commit()
