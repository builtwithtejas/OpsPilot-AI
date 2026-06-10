# backend/app/api/routes/incidents.py

import asyncio
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.schemas.incident_schema import IncidentCreate, IncidentResponse, IncidentUpdate
from app.services.incident_service import (
    create_incident, delete_incident, get_all_incidents,
    get_incident_by_id, update_incident, search_incidents,
)
from app.services.audit_service import log_action, get_audit_log
from app.services.notification_service import notify_all
from app.services.ai_service import generate_auto_fix
from app.services.gitlab_service import (
    create_fix_branch,
    commit_fix,
    create_fix_mr,
    get_latest_commit_sha,
    get_file_content,          # FIX: fetch actual .gitlab-ci.yml content
)
from app.utils.logger import logger

router = APIRouter(prefix="/incidents", tags=["Incidents"], dependencies=[Depends(require_api_key)])


@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(
    skip:   int = Query(0, ge=0),
    limit:  int = Query(100, ge=1, le=200),
    search: str = Query(""),
    db:     AsyncSession = Depends(get_db),
):
    if search.strip():
        return await search_incidents(db, search, skip=skip, limit=limit)
    return await get_all_incidents(db, skip=skip, limit=limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    inc = await get_incident_by_id(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return inc


@router.get("/{incident_id}/audit", summary="Audit log for an incident")
async def get_incident_audit(incident_id: int, db: AsyncSession = Depends(get_db)):
    if not await get_incident_by_id(db, incident_id):
        raise HTTPException(status_code=404, detail="Incident not found.")
    logs = await get_audit_log(db, incident_id)
    return [
        {"id": l.id, "action": l.action, "detail": l.detail, "actor": l.actor, "created_at": str(l.created_at)}
        for l in logs
    ]


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def add_incident(data: IncidentCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    inc = await create_incident(db, data)
    await log_action(db, inc.id, "created", f"Severity: {inc.severity}, Confidence: {inc.confidence}%")
    if inc.severity in ("High", "Critical"):
        background_tasks.add_task(notify_all, inc.id, inc.title, inc.severity, inc.description, inc.remediation)
    return inc


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def patch_incident(incident_id: int, data: IncidentUpdate, db: AsyncSession = Depends(get_db)):
    old = await get_incident_by_id(db, incident_id)
    if not old:
        raise HTTPException(status_code=404, detail="Incident not found.")
    old_status = old.status
    inc = await update_incident(db, incident_id, data)
    if data.status and data.status != old_status:
        await log_action(db, incident_id, "status_changed", f"{old_status} -> {data.status}")
    elif data.severity:
        await log_action(db, incident_id, "severity_changed", f"Severity set to {data.severity}")
    return inc


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    inc = await get_incident_by_id(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    await log_action(db, incident_id, "deleted", f"Title: {inc.title}")
    await delete_incident(db, incident_id)


# FIX: Single decorator (was duplicated), fetches real .gitlab-ci.yml content
@router.post(
    "/{incident_id}/autofix",
    summary="Generate an AI auto-fix MR for the incident",
    status_code=status.HTTP_200_OK,
)
async def autofix_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    inc = await get_incident_by_id(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    # Idempotent — return existing MR URL if already fixed
    if inc.autofix_mr_url:
        return {"mr_url": inc.autofix_mr_url, "already_exists": True}

    if not inc.pipeline_id:
        raise HTTPException(
            status_code=422,
            detail="This incident has no associated pipeline. Auto-fix requires a pipeline_id.",
        )

    project_id = settings.GITLAB_PROJECT_ID

    # FIX: Fetch actual .gitlab-ci.yml content so Groq has real context to fix
    current_yml_content = ""
    try:
        file_data = await get_file_content(project_id, ".gitlab-ci.yml")
        current_yml_content = file_data.get("content", "")
        logger.info("Fetched .gitlab-ci.yml — %d chars", len(current_yml_content))
    except Exception as exc:
        logger.warning("Could not fetch .gitlab-ci.yml — proceeding without it: %s", exc)
        # Fall back to a basic template so Groq still has something to work with
        current_yml_content = (
            "stages:\n  - build\n  - test\n  - deploy\n\n"
            "build-job:\n  stage: build\n  script:\n    - echo 'Building...'\n"
        )

    # generate_auto_fix() is synchronous — offload to thread pool
    fix = await asyncio.to_thread(
        generate_auto_fix,
        inc.description or "",
        inc.remediation or "",
        current_yml_content,   # FIX: real content, not empty string
    )

    if not fix or not fix.get("fixed_content"):
        raise HTTPException(
            status_code=502,
            detail="AI fix generation failed or returned empty content. Try again.",
        )

    try:
        logger.info(
            "AUTOFIX: incident=%s pipeline_id=%s project_id=%s",
            incident_id, inc.pipeline_id, project_id,
        )

        base_sha = await get_latest_commit_sha(project_id, ref="main")

        branch_name = await create_fix_branch(
            project_id=project_id,
            incident_id=incident_id,
            base_sha=base_sha,
        )

        await commit_fix(
            project_id=project_id,
            branch_name=branch_name,
            incident_id=incident_id,
            filename=fix["filename"],
            content=fix["fixed_content"],
            commit_message=fix["commit_message"],
        )

        mr = await create_fix_mr(
            project_id=project_id,
            branch_name=branch_name,
            incident_id=incident_id,
            title=f"[OpsPilot] Auto-fix for incident #{incident_id}",
            description=(
                f"## OpsPilot AI — Auto-Fix\n\n"
                f"**Incident #{incident_id}:** {inc.title}\n\n"
                f"**Fix:** {fix['fix_description']}\n\n"
                f"*Generated by OpsPilot AI x Groq llama-3.3-70b*"
            ),
        )

        mr_url = mr["url"]

    except Exception as exc:
        logger.warning("GitLab MR creation failed for incident #%d: %s", incident_id, exc)
        raise HTTPException(
            status_code=502,
            detail=f"GitLab MR creation failed: {exc}",
        )

    await update_incident(db, incident_id, IncidentUpdate(autofix_mr_url=mr_url))
    await log_action(db, incident_id, "autofix_created", f"MR: {mr_url}")

    return {"mr_url": mr_url, "already_exists": False}