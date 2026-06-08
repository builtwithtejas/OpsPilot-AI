# backend/app/services/audit_service.py
# FIX: Converted to async — uses AsyncSession and await db.execute(select(...)).
# All callers (incidents.py, agent_service.py) must await these functions.

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    incident_id: int,
    action: str,
    detail: str = "",
    actor: str = "system",
) -> AuditLog:
    entry = AuditLog(
        incident_id=incident_id,
        action=action,
        detail=detail,
        actor=actor,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_audit_log(db: AsyncSession, incident_id: int) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .filter(AuditLog.incident_id == incident_id)
        .order_by(AuditLog.created_at.desc())
    )
    return list(result.scalars().all())