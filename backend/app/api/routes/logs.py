from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.schemas.ai_schema import AnalyzeResponse
from app.schemas.incident_schema import IncidentCreate
from app.services.ai_service import analyze_logs
from app.services.incident_service import create_incident
from app.services.log_service import read_log_file, save_log_file
from app.utils.logger import logger

router = APIRouter(prefix="/logs", tags=["Logs"], dependencies=[Depends(require_api_key)])


@router.post("/upload", summary="Upload a log file (no analysis)")
async def upload_logs(file: UploadFile = File(...)):
    filepath = await save_log_file(file)
    return {"message": "File uploaded successfully", "filepath": str(filepath)}


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Upload and analyze a log file with AI",
)
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        filepath = await save_log_file(file)
        logs = read_log_file(filepath)

        if not logs.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uploaded file is empty — nothing to analyze.",
            )

        result = analyze_logs(logs)

        incident = create_incident(
            db,
            IncidentCreate(
                title=f"AI Detected: {result['summary'][:100]}",
                severity=result["severity"],
                status="Open",
                description=result["summary"],
                remediation=result["remediation"],
                confidence=result["confidence"],
            ),
        )

        logger.info("Incident #%d created from log upload (severity: %s)", incident.id, result["severity"])

        return AnalyzeResponse(
            incident_id=incident.id,
            summary=result["summary"],
            severity=result["severity"],
            root_cause=result["root_cause"],
            remediation=result["remediation"],
            confidence=result["confidence"],
            status=incident.status,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Log analysis pipeline failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(exc)}",
        )
