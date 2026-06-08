# C-2 FIX: The request-scoped DB session is closed before BackgroundTasks run.
# Solution: _run_agent_background now opens its OWN session using AsyncSessionLocal
# directly, instead of receiving the already-closed request session.

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.database import AsyncSessionLocal
from app.database.dependencies import get_db
from app.schemas.incident_schema import IncidentCreate
from app.services.audit_service import log_action
from app.services.incident_service import create_incident, get_incident_by_pipeline_id
from app.services.notification_service import send_slack_notification
from app.utils.logger import logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_github_signature(payload: bytes, signature: str | None) -> bool:
    if not settings.GITHUB_WEBHOOK_SECRET or not signature:
        return True
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _verify_gitlab_token(token: str | None) -> bool:
    if not settings.GITLAB_WEBHOOK_SECRET:
        return True
    return token == settings.GITLAB_WEBHOOK_SECRET


async def _run_agent_background(project_id: str, pipeline_id: int) -> None:
    """Run the full agent in the background with its own fresh DB session.

    C-2 FIX: We no longer accept a `db` parameter here.
    The request-scoped session is already closed by the time BackgroundTasks run.
    Instead, we open a new session scoped to this background task's lifetime.
    """
    async with AsyncSessionLocal() as db:
        try:
            from app.services.agent_service import run_agent
            logger.info(
                "Webhook: auto-triggering agent for project %s pipeline %s",
                project_id, pipeline_id,
            )
            result = await run_agent(
                db=db,
                project_id=project_id,
                pipeline_id=pipeline_id,
                triggered_by="gitlab-webhook",
            )
            logger.info(
                "Webhook: agent run %s completed — status: %s",
                result.run_id, result.status,
            )
        except Exception as exc:
            logger.error("Webhook: agent auto-run failed: %s", exc)


@router.post("/github", summary="Receive GitHub Actions webhook events")
async def github_webhook(
    request: Request,
    x_github_event:      str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()

    if not _verify_github_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature.")

    payload = await request.json()

    if x_github_event != "workflow_run":
        return {"message": f"Event '{x_github_event}' acknowledged but not processed."}

    run = payload.get("workflow_run", {})
    conclusion = run.get("conclusion")

    if conclusion != "failure":
        return {"message": f"Workflow conclusion '{conclusion}' — no incident needed."}

    workflow_name = run.get("name", "Unknown Workflow")
    branch        = run.get("head_branch", "unknown")
    commit        = (run.get("head_sha") or "")[:7]
    actor         = run.get("triggering_actor", {}).get("login", "unknown")
    run_url       = run.get("html_url", "")

    title = f"Workflow failure: {workflow_name} on {branch}"
    description = (
        f"GitHub Actions workflow '{workflow_name}' failed on branch '{branch}'. "
        f"Commit: {commit}. Triggered by: {actor}. "
        f"URL: {run_url}"
    )

    inc = await create_incident(db, IncidentCreate(
        title=title,
        severity="High",
        status="Open",
        description=description,
        remediation="1. Check the workflow logs at the URL above.\n2. Fix the failing step.\n3. Re-run the workflow.",
        confidence=85,
    ))

    await log_action(db, inc.id, "created", "Auto-created from GitHub webhook", actor="github-webhook")
    await send_slack_notification(inc.id, title, "High", description)

    logger.info("Webhook: created incident #%d for failed workflow '%s'", inc.id, workflow_name)
    return {"message": f"Incident #{inc.id} created for failed workflow.", "incident_id": inc.id}


@router.post("/gitlab", summary="Receive GitLab pipeline webhook events")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_gitlab_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not _verify_gitlab_token(x_gitlab_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitLab webhook token.",
        )

    payload = await request.json()

    object_kind = payload.get("object_kind")
    if object_kind != "pipeline":
        return {"message": f"Event '{object_kind}' acknowledged but not processed."}

    pipeline        = payload.get("object_attributes", {})
    pipeline_status = pipeline.get("status")
    if pipeline_status != "failed":
        return {"message": f"Pipeline status '{pipeline_status}' — no action needed."}

    pipeline_id  = pipeline.get("id")
    project      = payload.get("project", {})
    project_id   = str(project.get("id", ""))
    project_name = project.get("name", "unknown")
    branch       = pipeline.get("ref", "unknown")
    sha          = (pipeline.get("sha") or "")[:7]

    logger.info(
        "GitLab webhook: pipeline #%s failed in project %s (%s) on branch %s",
        pipeline_id, project_id, project_name, branch,
    )

    existing = await get_incident_by_pipeline_id(db, str(pipeline_id))
    if existing:
        logger.info("Webhook: pipeline #%s already has incident #%d — skipping", pipeline_id, existing.id)
        return {
            "message": f"Pipeline #{pipeline_id} already handled.",
            "incident_id": existing.id,
        }

    # C-2 FIX: pass only scalar values (project_id, pipeline_id), NOT the db session.
    # _run_agent_background opens its own session internally.
    background_tasks.add_task(
        _run_agent_background,
        project_id=project_id,
        pipeline_id=pipeline_id,
    )

    logger.info("Webhook: agent queued for pipeline #%s in project %s", pipeline_id, project_id)
    return {
        "message": f"Agent triggered for failed pipeline #{pipeline_id} in {project_name}.",
        "pipeline_id": pipeline_id,
        "project_id": project_id,
        "branch": branch,
        "commit": sha,
        "status": "agent_running",
    }
