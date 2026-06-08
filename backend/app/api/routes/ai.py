# backend/app/api/routes/ai.py
# FIX: Converted to async def, Session → AsyncSession, service calls awaited.

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.schemas.ai_schema import AnalyzeRequest, AnalyzeResponse
from app.schemas.incident_schema import IncidentCreate
from app.services.ai_service import analyze_logs
from app.services.incident_service import create_incident

router = APIRouter(prefix="/ai", tags=["AI"], dependencies=[Depends(require_api_key)])


@router.post("/analyze", response_model=AnalyzeResponse, summary="Analyze raw log text with AI")
async def analyze(request: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    result = analyze_logs(request.logs)

    incident = await create_incident(
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

    return AnalyzeResponse(
        incident_id=incident.id,
        summary=result["summary"],
        severity=result["severity"],
        root_cause=result["root_cause"],
        remediation=result["remediation"],
        confidence=result["confidence"],
        status=incident.status,
    )