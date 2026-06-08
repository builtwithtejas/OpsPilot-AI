# backend/app/services/incident_service.py
# FIX: All DB calls are now async — using await session.execute() instead
#      of sync db.query(). This is the pattern for every service file.
#
# Apply the same pattern to: audit_service.py, project_service.py,
# metrics_service.py — replace db.query(...) with await session.execute(select(...))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, delete as sql_delete
from app.models.incident import Incident
from app.schemas.incident_schema import IncidentCreate, IncidentUpdate


async def get_all_incidents(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Incident]:
    result = await db.execute(
        select(Incident).order_by(Incident.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def search_incidents(db: AsyncSession, query: str, skip: int = 0, limit: int = 50) -> list[Incident]:
    q = f"%{query}%"
    result = await db.execute(
        select(Incident)
        .filter(or_(
            Incident.title.ilike(q),
            Incident.description.ilike(q),
            Incident.remediation.ilike(q),
        ))
        .order_by(Incident.created_at.desc())
        .offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_incident_by_id(db: AsyncSession, incident_id: int) -> Incident | None:
    result = await db.execute(select(Incident).filter(Incident.id == incident_id))
    return result.scalar_one_or_none()


async def create_incident(db: AsyncSession, data: IncidentCreate) -> Incident:
    incident = Incident(**data.model_dump())
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident


async def update_incident(db: AsyncSession, incident_id: int, data: IncidentUpdate) -> Incident | None:
    incident = await get_incident_by_id(db, incident_id)
    if not incident:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    await db.commit()
    await db.refresh(incident)
    return incident


async def delete_incident(db: AsyncSession, incident_id: int) -> bool:
    incident = await get_incident_by_id(db, incident_id)
    if not incident:
        return False
    await db.delete(incident)
    await db.commit()
    return True


async def get_incident_by_pipeline_id(db: AsyncSession, pipeline_id: str) -> Incident | None:
    result = await db.execute(
        select(Incident).filter(Incident.pipeline_id == pipeline_id)
    )
    return result.scalar_one_or_none()


async def get_similar_incidents(db: AsyncSession, incident: Incident, limit: int = 3) -> list[Incident]:
    keywords = [
        w for w in incident.description.lower().split()
        if len(w) > 5 and w not in {"failed", "error", "pipeline", "stage", "during", "build"}
    ]
    if not keywords:
        return []

    kw_filters = [Incident.description.ilike(f"%{kw}%") for kw in keywords[:5]]
    # L FIX: or_(*[]) with an empty list raises a SQLAlchemy error.
    # Guard is already above (keywords is non-empty here), but kw_filters[:5]
    # could still be empty if keywords was somehow mutated; the explicit guard makes it safe.
    if not kw_filters:
        return []

    result = await db.execute(
        select(Incident)
        .filter(
            Incident.id != incident.id,
            Incident.severity == incident.severity,
            or_(*kw_filters),
        )
        .order_by(Incident.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_incidents_summary_for_memory(db: AsyncSession, limit: int = 20) -> str:
    result = await db.execute(
        select(Incident)
        .filter(Incident.confidence > 0)
        .order_by(Incident.created_at.desc())
        .limit(limit)
    )
    incidents = list(result.scalars().all())

    if not incidents:
        return "No historical incidents available."

    lines = ["Recent incident history for pattern analysis:\n"]
    for inc in incidents:
        lines.append(
            f"- [{inc.severity}] {inc.title} | "
            f"Root cause: {inc.description[:100]} | "
            f"Pipeline: {inc.pipeline_id or 'unknown'} | "
            f"Date: {inc.created_at.strftime('%Y-%m-%d')}"
        )
    return "\n".join(lines)
