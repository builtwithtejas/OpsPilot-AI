# backend/app/api/routes/projects.py
# FIX: All routes converted to async def, Session → AsyncSession,
#      all service calls awaited.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.schemas.project_schema import ProjectCreate, ProjectOut
from app.services.project_service import (
    get_all_projects,
    get_project_by_gitlab_id,
    create_project,
    delete_project,
    toggle_project,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    return await get_all_projects(db)


@router.post("/", response_model=ProjectOut)
async def register_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    existing = await get_project_by_gitlab_id(db, data.gitlab_project_id)
    if existing:
        raise HTTPException(status_code=409, detail="Project already registered.")
    return await create_project(db, data)


@router.delete("/{project_id}")
async def remove_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    if not await delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"message": f"Project {project_id} removed."}


@router.patch("/{project_id}/toggle")
async def toggle_project_active(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    project = await toggle_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"id": project.id, "active": project.active}