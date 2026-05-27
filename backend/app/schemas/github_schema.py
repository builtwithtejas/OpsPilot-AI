from pydantic import BaseModel
from typing import Any


class WorkflowRun(BaseModel):
    workflow: str
    status: str
    conclusion: str | None
    branch: str
    commit: str
    actor: str
    run_number: int
    url: str
    created_at: str


class RepoStats(BaseModel):
    name: str
    stars: int
    forks: int
    open_issues: int
    watchers: int
    default_branch: str
    last_commit: str
    last_commit_message: str


class AnalyticsResponse(BaseModel):
    analysis: str
    incident_trends: list[dict[str, Any]]
    deployment_activity: list[dict[str, Any]]
    severity_distribution: list[dict[str, Any]]
    suggested_commands: list[str]
    stats: dict[str, Any]   # now includes success_rate float
