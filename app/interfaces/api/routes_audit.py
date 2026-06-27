from fastapi import APIRouter, Depends

from app.application.audit_use_cases import AuditUseCases
from app.domain.entities import User
from app.interfaces.api.dependencies import current_user, get_audit_repository

router = APIRouter()


def get_audit_use_cases(audits=Depends(get_audit_repository)) -> AuditUseCases:
    return AuditUseCases(audits)


@router.get("/audit")
def list_audit(
    audit: AuditUseCases = Depends(get_audit_use_cases),
    user: User = Depends(current_user),
) -> list[dict]:
    rows = audit.list_for_user(user.id)
    return [
        {
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
