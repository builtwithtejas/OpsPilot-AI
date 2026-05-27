from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    logs: str = Field(..., min_length=10, description="Raw log content to analyze")


class AnalyzeResponse(BaseModel):
    incident_id: int
    summary: str
    severity: str
    root_cause: str
    remediation: str
    confidence: int
    status: str
