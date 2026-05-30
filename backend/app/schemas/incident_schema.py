from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SeverityLevel = Literal["Low", "Medium", "High", "Critical"]
IncidentStatus = Literal["Open", "In Progress", "Resolved", "Closed"]


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    severity: SeverityLevel
    status: IncidentStatus = "Open"

    description: str = Field(..., min_length=10)
    remediation: str = Field(..., min_length=5)

    confidence: int = Field(..., ge=0, le=100)

    # NEW
    source: str = "GitLab"
    pipeline_id: int | None = None
    gitlab_issue_url: str | None = None


class IncidentUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    severity: SeverityLevel | None = None
    status: IncidentStatus | None = None

    description: str | None = None
    remediation: str | None = None

    confidence: int | None = Field(None, ge=0, le=100)

    source: str | None = None
    pipeline_id: int | None = None
    gitlab_issue_url: str | None = None


class IncidentResponse(BaseModel):
    id: int

    title: str
    severity: str
    status: str

    description: str
    remediation: str
    confidence: int

    source: str | None = None
    pipeline_id: int | None = None
    gitlab_issue_url: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}