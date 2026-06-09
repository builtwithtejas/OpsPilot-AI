# backend/app/api/routes/agent.py
from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.services.agent_service import run_agent
from app.services.ai_service import get_adk_agent_info          # NEW
from app.services.gitlab_service import get_failed_pipelines, get_pipeline_jobs
from app.utils.logger import logger

router = APIRouter(prefix="/agent", tags=["Agent"], dependencies=[Depends(require_api_key)])


class AgentTriggerRequest(BaseModel):
    project_id: str
    pipeline_id: int | None = None


class GitLabProjectRequest(BaseModel):
    project_id: str


# ── Existing endpoints (unchanged) ───────────────────────────────

@router.post("/run", summary="Trigger the full OpsPilot autonomous agent pipeline")
async def trigger_agent(
    request: AgentTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs the full 7-step agent:
    Detect → Gather logs → Gemini analysis → Record incident → GitLab issue + MR comment → Notify → Duo
    """
    if not request.project_id:
        raise HTTPException(status_code=400, detail="project_id is required.")
    run = await run_agent(db, project_id=request.project_id, pipeline_id=request.pipeline_id)
    return {
        "run_id":           run.run_id,
        "status":           run.status,
        "incident_id":      run.incident_id,
        "gitlab_issue_url": run.gitlab_issue_url,
        "steps": [
            {
                "name":   s.name,
                "status": s.status,
                "result": s.result,
                "error":  s.error,
            }
            for s in run.steps
        ],
    }


@router.get("/pipelines/{project_id}", summary="List recent failed GitLab pipelines")
async def list_failed_pipelines(project_id: str):
    try:
        pipelines = await get_failed_pipelines(project_id, limit=10)
        return {"project_id": project_id, "failed_pipelines": pipelines}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"GitLab API error: {exc}")


@router.get("/pipelines/{project_id}/{pipeline_id}/jobs", summary="Get jobs for a pipeline")
async def list_pipeline_jobs(project_id: str, pipeline_id: int):
    try:
        jobs = await get_pipeline_jobs(project_id, pipeline_id)
        return {"pipeline_id": pipeline_id, "jobs": jobs}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"GitLab API error: {exc}")


# ── NEW: Google ADK agent info endpoint ───────────────────────────

@router.get("/info", summary="Google ADK agent metadata")
async def agent_info():
    """
    Returns OpsPilot ADK agent info — framework, model, tools, status.
    Shows judges that OpsPilot is built on Google Agent Development Kit.
    """
    return get_adk_agent_info()