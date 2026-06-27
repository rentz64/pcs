from app.domain.entities import AuditEntry
from app.domain.repositories import AuditRepository


class AuditUseCases:
    def __init__(self, audits: AuditRepository):
        self.audits = audits

    def list_for_user(self, user_id: int) -> list[AuditEntry]:
        return self.audits.list_for_user(user_id, limit=100)
