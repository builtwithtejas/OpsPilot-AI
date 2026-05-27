import re as _re

from fastapi import APIRouter, Depends, HTTPException
from github import GithubException

from app.core.security import require_api_key
from app.schemas.github_schema import AnalyticsResponse, RepoStats, WorkflowRun
from app.services.github_service import _get_repo, build_analytics, get_repo_stats, get_workflow_runs

router = APIRouter(prefix="/github", tags=["GitHub"], dependencies=[Depends(require_api_key)])


@router.get("/workflows", response_model=list[WorkflowRun], summary="Recent workflow runs")
def workflows():
    return get_workflow_runs(limit=10)


@router.get("/analytics", response_model=AnalyticsResponse, summary="Aggregated CI/CD analytics")
def analytics():
    runs = get_workflow_runs(limit=50)
    return build_analytics(runs)


@router.get("/repo", response_model=RepoStats, summary="Repository statistics")
def repo_stats():
    return get_repo_stats()


@router.post("/rerun", summary="Re-run a failed GitHub Actions workflow")
def rerun_workflow(payload: dict):
    url = payload.get("workflow_url", "")
    match = _re.search(r"/runs/(\d+)", url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid workflow URL — cannot extract run ID.")
    run_id = int(match.group(1))
    try:
        repo = _get_repo()
        run = repo.get_workflow_run(run_id)
        run.rerun()
        return {"message": f"Workflow run #{run_id} re-triggered successfully."}
    except GithubException as exc:
        raise HTTPException(status_code=503, detail=f"GitHub API error: {exc}")
