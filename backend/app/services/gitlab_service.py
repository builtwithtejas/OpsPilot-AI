from __future__ import annotations

import httpx
from app.core.config import settings
from app.utils.logger import logger


def _headers() -> dict:
    return {"PRIVATE-TOKEN": settings.GITLAB_TOKEN, "Content-Type": "application/json"}


def _base() -> str:
    return f"{settings.GITLAB_BASE_URL}/api/v4"


async def create_gitlab_issue(
    project_id: str | int,
    title: str,
    description: str,
    labels: list[str] | None = None,
) -> dict:
    """Create a GitLab issue for an incident."""
    payload = {
        "title": title,
        "description": description,
        "labels": ",".join(labels or ["opspilot", "incident", "ci-cd"]),
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_base()}/projects/{project_id}/issues",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("GitLab issue #%s created: %s", data.get("iid"), title)
        return {"iid": data["iid"], "url": data["web_url"], "title": data["title"]}


async def get_failed_pipelines(project_id: str | int, limit: int = 5) -> list[dict]:
    """Fetch recent failed CI/CD pipelines from GitLab."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base()}/projects/{project_id}/pipelines",
            params={"status": "failed", "per_page": limit},
            headers=_headers(),
        )
        resp.raise_for_status()
        pipelines = resp.json()
        return [
            {
                "id": p["id"],
                "status": p["status"],
                "ref": p["ref"],
                "sha": p["sha"][:7],
                "web_url": p["web_url"],
                "created_at": p["created_at"],
            }
            for p in pipelines
        ]


async def get_pipeline_jobs(project_id: str | int, pipeline_id: int) -> list[dict]:
    """Get jobs for a specific pipeline to identify which step failed."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base()}/projects/{project_id}/pipelines/{pipeline_id}/jobs",
            headers=_headers(),
        )
        resp.raise_for_status()
        jobs = resp.json()
        logger.info("GitLab raw jobs response: %s", jobs)
        return [
            {
                "id": j["id"],
                "name": j["name"],
                "stage": j["stage"],
                "status": j["status"],
                "failure_reason": j.get("failure_reason"),
                "web_url": j["web_url"],
            }
            for j in jobs
            if j["status"] in ("failed", "success", "running")
        ]


async def get_job_trace(
    project_id: str | int,
    job_id: int,
) -> str:
    """
    Fetch raw GitLab job logs.
    """

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{_base()}/projects/{project_id}/jobs/{job_id}/trace",
            headers=_headers(),
        )

        resp.raise_for_status()

        return resp.text



async def post_pipeline_comment(
    project_id: str | int,
    pipeline_id: int,
    comment: str,
) -> dict:
    """Post a comment on the merge request associated with this pipeline."""
    # Get MR associated with pipeline
    async with httpx.AsyncClient(timeout=10) as client:
        mr_resp = await client.get(
            f"{_base()}/projects/{project_id}/pipelines/{pipeline_id}/merge_requests",
            headers=_headers(),
        )
        if mr_resp.status_code != 200 or not mr_resp.json():
            return {"message": "No MR found for this pipeline"}

        mr_iid = mr_resp.json()[0]["iid"]
        note_resp = await client.post(
            f"{_base()}/projects/{project_id}/merge_requests/{mr_iid}/notes",
            json={"body": comment},
            headers=_headers(),
        )
        note_resp.raise_for_status()
        logger.info("Posted OpsPilot comment on MR !%s", mr_iid)
        return {"mr_iid": mr_iid, "note_id": note_resp.json()["id"]}
