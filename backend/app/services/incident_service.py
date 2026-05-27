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
