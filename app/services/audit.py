from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: int | None,
    action: str,
    before_json: dict | None = None,
    after_json: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_json=before_json,
            after_json=after_json,
        )
    )
