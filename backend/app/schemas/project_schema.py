from pydantic import BaseModel
from datetime import datetime


class ProjectCreate(BaseModel):
    gitlab_project_id: str
    name: str
    description: str | None = None
    webhook_secret: str | None = None


class ProjectOut(BaseModel):
    id: int
    gitlab_project_id: str
    name: str
    description: str | None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}