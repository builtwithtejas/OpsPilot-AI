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
