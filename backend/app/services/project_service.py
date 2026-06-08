# backend/app/services/project_service.py
# FIX: Converted to async — uses AsyncSession and await db.execute(select(...)).

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.monitored_project import MonitoredProject
from app.schemas.project_schema import ProjectCreate


async def get_all_projects(db: AsyncSession) -> list[MonitoredProject]:
    result = await db.execute(
        select(MonitoredProject).order_by(MonitoredProject.created_at.desc())
    )
    return list(result.scalars().all())


async def get_project_by_gitlab_id(
    db: AsyncSession, gitlab_project_id: str
) -> MonitoredProject | None:
    result = await db.execute(
        select(MonitoredProject).filter(
            MonitoredProject.gitlab_project_id == gitlab_project_id
        )
    )
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, data: ProjectCreate) -> MonitoredProject:
    project = MonitoredProject(**data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    result = await db.execute(
        select(MonitoredProject).filter(MonitoredProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        return False
    await db.delete(project)
    await db.commit()
    return True


async def toggle_project(db: AsyncSession, project_id: int) -> MonitoredProject | None:
    result = await db.execute(
        select(MonitoredProject).filter(MonitoredProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        return None
    project.active = not project.active
    await db.commit()
    await db.refresh(project)
    return project