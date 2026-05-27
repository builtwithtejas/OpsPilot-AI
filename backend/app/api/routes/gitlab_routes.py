from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import require_api_key
from app.services.gitlab_service import (
    create_gitlab_issue,
    get_failed_pipelines,
    get_pipeline_jobs,
)

router = APIRouter(prefix="/gitlab", tags=["GitLab MCP"], dependencies=[Depends(require_api_key)])


class IssueRequest(BaseModel):
    project_id: str
    title: str
    description: str
    labels: list[str] = ["opspilot", "incident"]


@router.get("/{project_id}/pipelines/failed", summary="Failed pipelines from GitLab")
async def failed_pipelines(project_id: str, limit: int = 5):
    try:
        return await get_failed_pipelines(project_id, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/{project_id}/pipelines/{pipeline_id}/jobs", summary="Jobs for a pipeline")
async def pipeline_jobs(project_id: str, pipeline_id: int):
    try:
        return await get_pipeline_jobs(project_id, pipeline_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/issue", summary="Create a GitLab issue")
async def create_issue(req: IssueRequest):
    try:
        return await create_gitlab_issue(req.project_id, req.title, req.description, req.labels)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
