from sqlalchemy.orm import Session
from app.models.monitored_project import MonitoredProject
from app.schemas.project_schema import ProjectCreate


def get_all_projects(db: Session) -> list[MonitoredProject]:
    return db.query(MonitoredProject).order_by(MonitoredProject.created_at.desc()).all()


def get_project_by_gitlab_id(db: Session, gitlab_project_id: str) -> MonitoredProject | None:
    return db.query(MonitoredProject).filter(
        MonitoredProject.gitlab_project_id == gitlab_project_id
    ).first()


def create_project(db: Session, data: ProjectCreate) -> MonitoredProject:
    project = MonitoredProject(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> bool:
    project = db.query(MonitoredProject).filter(MonitoredProject.id == project_id).first()
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True


def toggle_project(db: Session, project_id: int) -> MonitoredProject | None:
    project = db.query(MonitoredProject).filter(MonitoredProject.id == project_id).first()
    if not project:
        return None
    project.active = not project.active
    db.commit()
    db.refresh(project)
    return project