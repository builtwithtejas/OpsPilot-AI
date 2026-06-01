from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.schemas.incident_schema import IncidentCreate, IncidentResponse, IncidentUpdate
from app.services.incident_service import (
    create_incident, delete_incident, get_all_incidents,
    get_incident_by_id, update_incident, search_incidents,
)
from app.services.audit_service import log_action, get_audit_log
from app.services.notification_service import notify_all

router = APIRouter(prefix="/incidents", tags=["Incidents"], dependencies=[Depends(require_api_key)])


@router.get("/", response_model=list[IncidentResponse])
def list_incidents(
    skip:   int = Query(0, ge=0),
    limit:  int = Query(100, ge=1, le=200),
    search: str = Query(""),
    db:     Session = Depends(get_db),
):
    if search.strip():
        return search_incidents(db, search, skip=skip, limit=limit)
    return get_all_incidents(db, skip=skip, limit=limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = get_incident_by_id(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return inc


@router.get("/{incident_id}/audit", summary="Audit log for an incident")
def get_incident_audit(incident_id: int, db: Session = Depends(get_db)):
    if not get_incident_by_id(db, incident_id):
        raise HTTPException(status_code=404, detail="Incident not found.")
    logs = get_audit_log(db, incident_id)
    return [{"id": l.id, "action": l.action, "detail": l.detail, "actor": l.actor, "created_at": str(l.created_at)} for l in logs]


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def add_incident(data: IncidentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    inc = create_incident(db, data)
    log_action(db, inc.id, "created", f"Severity: {inc.severity}, Confidence: {inc.confidence}%")
    # Fire Slack + email for High / Critical in background (non-blocking)
    if inc.severity in ("High", "Critical"):
        background_tasks.add_task(notify_all, inc.id, inc.title, inc.severity, inc.description, inc.remediation)
    return inc


@router.patch("/{incident_id}", response_model=IncidentResponse)
def patch_incident(incident_id: int, data: IncidentUpdate, db: Session = Depends(get_db)):
    old = get_incident_by_id(db, incident_id)
    if not old:
        raise HTTPException(status_code=404, detail="Incident not found.")
    old_status = old.status
    inc = update_incident(db, incident_id, data)
    if data.status and data.status != old_status:
        log_action(db, incident_id, "status_changed", f"{old_status} → {data.status}")
    elif data.severity:
        log_action(db, incident_id, "severity_changed", f"Severity set to {data.severity}")
    return inc


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = get_incident_by_id(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    log_action(db, incident_id, "deleted", f"Title: {inc.title}")
    delete_incident(db, incident_id)

from app.services.gitlab_service import (
    create_fix_branch, commit_fix, create_fix_mr,
    get_file_content, get_latest_commit_sha,
)
from app.services.ai_service import generate_auto_fix


@router.post("/{incident_id}/autofix", summary="Generate and open an auto-fix MR")
async def auto_fix_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = get_incident_by_id(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    if not inc.pipeline_id:
        raise HTTPException(status_code=400, detail="No pipeline_id on this incident.")
    if inc.autofix_mr_url:
        return {"message": "Auto-fix MR already exists.", "mr_url": inc.autofix_mr_url}

    project_id = "82734152"

    # Step 1 — get current .gitlab-ci.yml
    file_data = await get_file_content(project_id, ".gitlab-ci.yml")
    current_content = file_data.get("content", "# empty")

    # Step 2 — Gemini generates the fix
    fix = generate_auto_fix(
        root_cause=inc.description,
        remediation=inc.remediation,
        current_file_content=current_content,
    )
    if not fix or not fix.get("fixed_content"):
        raise HTTPException(status_code=500, detail="Gemini could not generate a fix.")

    # Step 3 — create branch from latest main
    sha = await get_latest_commit_sha(project_id)
    branch = await create_fix_branch(project_id, incident_id=inc.id, base_sha=sha)

    # Step 4 — commit the fix
    await commit_fix(
        project_id=project_id,
        branch_name=branch,
        incident_id=inc.id,
        filename=fix["filename"],
        content=fix["fixed_content"],
        commit_message=fix["commit_message"],
    )

    # Step 5 — open MR
    mr = await create_fix_mr(
        project_id=project_id,
        branch_name=branch,
        incident_id=inc.id,
        title=f"🤖 OpsPilot Auto-Fix: Incident #{inc.id}",
        description=(
            f"## 🤖 OpsPilot AI — Auto-Fix\n\n"
            f"**Incident:** #{inc.id}\n"
            f"**Fix:** {fix['fix_description']}\n\n"
            f"### Root Cause\n{inc.description}\n\n"
            f"### Remediation Applied\n{inc.remediation}\n\n"
            f"*Auto-generated by OpsPilot AI × Gemini 2.5 Flash*"
        ),
    )

    # Step 6 — store MR URL on incident
    inc.autofix_mr_url = mr["url"]
    db.commit()
    log_action(db, inc.id, "autofix_created", f"Auto-fix MR: {mr['url']}", actor="agent")

    return {
        "message": "Auto-fix MR created successfully.",
        "mr_url": mr["url"],
        "mr_iid": mr["iid"],
        "branch": branch,
        "fix_description": fix["fix_description"],
    }