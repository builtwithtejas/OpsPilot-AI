from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(db: Session, incident_id: int, action: str, detail: str = "", actor: str = "system") -> AuditLog:
    entry = AuditLog(incident_id=incident_id, action=action, detail=detail, actor=actor)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_log(db: Session, incident_id: int) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.incident_id == incident_id)
        .order_by(AuditLog.created_at.desc())
        .all()
    )
