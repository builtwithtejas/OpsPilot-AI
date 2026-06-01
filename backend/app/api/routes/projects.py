from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.schemas.project_schema import ProjectCreate, ProjectOut
from app.services.project_service import (
    get_all_projects, get_project_by_gitlab_id,
    create_project, delete_project, toggle_project
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), _=Depends(require_api_key)):
    return get_all_projects(db)


@router.post("/", response_model=ProjectOut)
def register_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    _=Depends(require_api_key),
):
    existing = get_project_by_gitlab_id(db, data.gitlab_project_id)
    if existing:
        raise HTTPException(status_code=409, detail="Project already registered.")
    return create_project(db, data)


@router.delete("/{project_id}")
def remove_project(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_api_key),
):
    if not delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"message": f"Project {project_id} removed."}


@router.patch("/{project_id}/toggle")
def toggle_project_active(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_api_key),
):
    project = toggle_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"id": project.id, "active": project.active}