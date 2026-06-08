# backend/app/api/routes/incidents.py
#
# FIX R-3: generate_auto_fix() is a synchronous Gemini call.
# Calling it directly inside an async route blocks the event loop.
# Wrapped with asyncio.to_thread() so it runs in a thread pool.

import asyncio

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
from app.services.gitlab_service import create_fix_mr_workflow
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


@router.post(
    "/{incident_id}/autofix",
    summary="Generate an AI auto-fix MR for the incident",
    status_code=status.HTTP_200_OK,
)
async def autofix_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generates a Gemini-powered fix for the failing CI file and opens a GitLab MR.

    Returns:
        { "mr_url": "https://gitlab.com/..." }

    Raises:
        404 if incident not found
        422 if the incident has no associated pipeline (nothing to fix)
        502 if AI generation or GitLab MR creation fails
    """
    inc = await get_incident_by_id(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    if not inc.pipeline_id:
        raise HTTPException(
            status_code=422,
            detail="This incident has no associated pipeline. Auto-fix requires a pipeline_id.",
        )

    # FIX R-3: generate_auto_fix() calls the Gemini SDK synchronously.
    # Running it directly in an async route blocks the entire event loop.
    # asyncio.to_thread() offloads it to a thread pool so other requests
    # are not stalled during the Gemini API call (which can take 2–5 seconds).
    fix = await asyncio.to_thread(
        generate_auto_fix,
        inc.description or "",
        inc.remediation or "",
        "",  # current_file_content — GitLab service fetches the real file
    )

    if not fix or not fix.get("fixed_content"):
        raise HTTPException(
            status_code=502,
            detail="AI fix generation failed or returned empty content. Try again.",
        )

    try:
      mr_url = await create_fix_mr_workflow(
    project_id=str(inc.pipeline_id),
    filename=fix["filename"],
    fixed_content=fix["fixed_content"],
    commit_message=fix["commit_message"],
    description=fix["fix_description"],
    incident_id=incident_id,
)
    except Exception as exc:
        logger.warning("GitLab MR creation failed for incident #%d: %s", incident_id, exc)
        raise HTTPException(
            status_code=502,
            detail=f"GitLab MR creation failed: {exc}",
        )

    await update_incident(db, incident_id, IncidentUpdate(autofix_mr_url=mr_url))
    await log_action(db, incident_id, "autofix_created", f"MR: {mr_url}")

    return {"mr_url": mr_url}