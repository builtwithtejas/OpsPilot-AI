from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.schemas.incident_schema import IncidentCreate
from app.services.audit_service import log_action
from app.services.incident_service import create_incident
from app.services.notification_service import send_slack_notification
from app.utils.logger import logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_github_signature(payload: bytes, signature: str | None) -> bool:
    """Verify the X-Hub-Signature-256 header from GitHub."""
    if not settings.GITHUB_WEBHOOK_SECRET or not signature:
        return True   # skip verification if secret not configured
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github", summary="Receive GitHub Actions webhook events")
async def github_webhook(
    request: Request,
    x_github_event:    str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
    db: Session = Depends(get_db),
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

    inc = create_incident(db, IncidentCreate(
        title=title,
        severity="High",
        status="Open",
        description=description,
        remediation="1. Check the workflow logs at the URL above.\n2. Fix the failing step.\n3. Re-run the workflow.",
        confidence=85,
    ))

    log_action(db, inc.id, "created", "Auto-created from GitHub webhook", actor="github-webhook")
    await send_slack_notification(inc.id, title, "High", description)

    logger.info("Webhook: created incident #%d for failed workflow '%s'", inc.id, workflow_name)
    return {"message": f"Incident #{inc.id} created for failed workflow.", "incident_id": inc.id}
