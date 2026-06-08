# C-1 FIX: All GitHub SDK calls are synchronous (PyGithub has no async support).
# Wrapping them with asyncio.to_thread() runs them in a thread pool,
# preventing them from blocking the async event loop under load.

import asyncio
import re as _re

from fastapi import APIRouter, Depends, HTTPException
from github import GithubException

from app.core.security import require_api_key
from app.schemas.github_schema import AnalyticsResponse, RepoStats, WorkflowRun
from app.services.github_service import _get_repo, build_analytics, get_repo_stats, get_workflow_runs

router = APIRouter(prefix="/github", tags=["GitHub"], dependencies=[Depends(require_api_key)])


@router.get("/workflows", response_model=list[WorkflowRun], summary="Recent workflow runs")
async def workflows():
    return await asyncio.to_thread(get_workflow_runs, 10)


@router.get("/analytics", response_model=AnalyticsResponse, summary="Aggregated CI/CD analytics")
async def analytics():
    runs = await asyncio.to_thread(get_workflow_runs, 50)
    return build_analytics(runs)


@router.get("/repo", response_model=RepoStats, summary="Repository statistics")
async def repo_stats():
    return await asyncio.to_thread(get_repo_stats)


@router.post("/rerun", summary="Re-run a failed GitHub Actions workflow")
async def rerun_workflow(payload: dict):
    url = payload.get("workflow_url", "")
    match = _re.search(r"/runs/(\d+)", url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid workflow URL — cannot extract run ID.")
    run_id = int(match.group(1))

    def _do_rerun():
        repo = _get_repo()
        run = repo.get_workflow_run(run_id)
        run.rerun()

    try:
        await asyncio.to_thread(_do_rerun)
        return {"message": f"Workflow run #{run_id} re-triggered successfully."}
    except GithubException as exc:
        raise HTTPException(status_code=503, detail=f"GitHub API error: {exc}")
