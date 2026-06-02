from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.incident import Incident
from app.schemas.incident_schema import IncidentCreate, IncidentUpdate


def get_all_incidents(db: Session, skip: int = 0, limit: int = 50) -> list[Incident]:
    return db.query(Incident).order_by(Incident.created_at.desc()).offset(skip).limit(limit).all()


def search_incidents(db: Session, query: str, skip: int = 0, limit: int = 50) -> list[Incident]:
    q = f"%{query}%"
    return (
        db.query(Incident)
        .filter(or_(Incident.title.ilike(q), Incident.description.ilike(q), Incident.remediation.ilike(q)))
        .order_by(Incident.created_at.desc())
        .offset(skip).limit(limit).all()
    )


def get_incident_by_id(db: Session, incident_id: int) -> Incident | None:
    return db.query(Incident).filter(Incident.id == incident_id).first()


def create_incident(db: Session, data: IncidentCreate) -> Incident:
    incident = Incident(**data.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident(db: Session, incident_id: int, data: IncidentUpdate) -> Incident | None:
    incident = get_incident_by_id(db, incident_id)
    if not incident:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    return incident


def delete_incident(db: Session, incident_id: int) -> bool:
    incident = get_incident_by_id(db, incident_id)
    if not incident:
        return False
    db.delete(incident)
    db.commit()
    return True

def get_incident_by_pipeline_id(db: Session, pipeline_id: str):
    return db.query(Incident).filter(Incident.pipeline_id == pipeline_id).first()


def get_similar_incidents(db: Session, incident: Incident, limit: int = 3) -> list[Incident]:
    """
    Agent memory — find similar past incidents by:
    1. Same severity
    2. Overlapping keywords in title/description
    3. Exclude the incident itself
    """
    keywords = [
        w for w in incident.description.lower().split()
        if len(w) > 5 and w not in {"failed", "error", "pipeline", "stage", "during", "build"}
    ]
    if not keywords:
        return []

    filters = [
        Incident.id != incident.id,
        Incident.severity == incident.severity,
        or_(*[Incident.description.ilike(f"%{kw}%") for kw in keywords[:5]])
    ]

    return (
        db.query(Incident)
        .filter(*filters)
        .order_by(Incident.created_at.desc())
        .limit(limit)
        .all()
    )


def get_incidents_summary_for_memory(db: Session, limit: int = 20) -> str:
    """
    Format recent incidents as context for Gemini agent memory.
    Used to ground analysis against historical patterns.
    """
    incidents = (
        db.query(Incident)
        .filter(Incident.confidence > 0)
        .order_by(Incident.created_at.desc())
        .limit(limit)
        .all()
    )
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