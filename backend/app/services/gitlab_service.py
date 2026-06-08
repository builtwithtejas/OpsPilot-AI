from __future__ import annotations

from urllib.parse import quote

import httpx
from app.core.config import settings
from app.utils.logger import logger


def _headers() -> dict:
    return {"PRIVATE-TOKEN": settings.GITLAB_TOKEN, "Content-Type": "application/json"}


def _base() -> str:
    return f"{settings.GITLAB_BASE_URL}/api/v4"


def _encode_project(project_id: str | int) -> str:
    """
    GitLab API requires namespace/project to be URL-encoded (%2F not /).
    Numeric IDs pass through unchanged.
    e.g. "opspilot-ai-hackathon/opspilot-demo" → "opspilot-ai-hackathon%2Fopspilot-demo"
         82734152 → "82734152"
    """
    return quote(str(project_id), safe="")


async def create_gitlab_issue(
    project_id: str | int,
    title: str,
    description: str,
    labels: list[str] | None = None,
) -> dict:
    """Create a GitLab issue for an incident."""
    pid = _encode_project(project_id)
    payload = {
        "title": title,
        "description": description,
        "labels": ",".join(labels or ["opspilot", "incident", "ci-cd"]),
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_base()}/projects/{pid}/issues",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("GitLab issue #%s created: %s", data.get("iid"), title)
        return {"iid": data["iid"], "url": data["web_url"], "title": data["title"]}


async def get_failed_pipelines(project_id: str | int, limit: int = 5) -> list[dict]:
    """Fetch recent failed CI/CD pipelines from GitLab."""
    pid = _encode_project(project_id)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base()}/projects/{pid}/pipelines",
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
    pid = _encode_project(project_id)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base()}/projects/{pid}/pipelines/{pipeline_id}/jobs",
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
    """Fetch raw GitLab job logs."""
    pid = _encode_project(project_id)
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{_base()}/projects/{pid}/jobs/{job_id}/trace",
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
    pid = _encode_project(project_id)
    async with httpx.AsyncClient(timeout=10) as client:
        mr_resp = await client.get(
            f"{_base()}/projects/{pid}/pipelines/{pipeline_id}/merge_requests",
            headers=_headers(),
        )
        if mr_resp.status_code != 200 or not mr_resp.json():
            return {"message": "No MR found for this pipeline"}

        mr_iid = mr_resp.json()[0]["iid"]
        note_resp = await client.post(
            f"{_base()}/projects/{pid}/merge_requests/{mr_iid}/notes",
            json={"body": comment},
            headers=_headers(),
        )
        note_resp.raise_for_status()
        logger.info("Posted OpsPilot comment on MR !%s", mr_iid)
        return {"mr_iid": mr_iid, "note_id": note_resp.json()["id"]}


async def trigger_duo_agent(project_id: str, incident_summary: str, issue_url: str) -> dict:
    """Notify the GitLab Duo Agent Platform about a new incident."""
    if not settings.GITLAB_MCP_URL or not settings.GITLAB_AGENT_ID:
        logger.warning("GitLab Duo agent not configured — skipping")
        return {"skipped": True}
    try:
        payload = {
            "content": (
                f"New CI/CD incident detected in project {project_id}.\n"
                f"Summary: {incident_summary}\n"
                f"GitLab Issue: {issue_url}\n"
                f"Please analyse and suggest additional remediation steps."
            )
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.GITLAB_BASE_URL}/api/v4/ai/agents/{settings.GITLAB_AGENT_ID}/chat",
                json=payload,
                headers=_headers(),
            )
            if resp.status_code in (200, 201):
                logger.info("GitLab Duo agent notified for project %s", project_id)
                return {"notified": True, "agent_id": settings.GITLAB_AGENT_ID}
            else:
                logger.warning("Duo agent returned %s: %s", resp.status_code, resp.text)
                return {"notified": False, "status": resp.status_code}
    except Exception as exc:
        logger.warning("Duo agent notification failed (non-fatal): %s", exc)
        return {"error": str(exc)}
async def create_fix_branch(
    project_id: str | int,
    incident_id: int,
    base_sha: str,
) -> str:
    """Create a new branch for the auto-fix MR."""
    pid = _encode_project(project_id)
    branch_name = f"opspilot/fix-incident-{incident_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_base()}/projects/{pid}/repository/branches",
            json={"branch": branch_name, "ref": base_sha},
            headers=_headers(),
        )
        if resp.status_code == 400 and "already exists" in resp.text:
            logger.info("Branch %s already exists — reusing", branch_name)
            return branch_name
        resp.raise_for_status()
        logger.info("Created fix branch: %s", branch_name)
        return branch_name


async def commit_fix(
    project_id: str | int,
    branch_name: str,
    incident_id: int,
    filename: str,
    content: str,
    commit_message: str,
) -> dict:
    """Commit the Gemini-generated fix to the branch."""
    pid = _encode_project(project_id)
    payload = {
        "branch": branch_name,
        "commit_message": commit_message,
        "actions": [
            {
                "action": "update",
                "file_path": filename,
                "content": content,
            }
        ],
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{_base()}/projects/{pid}/repository/commits",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("Committed fix to branch %s: %s", branch_name, commit_message)
        return {"sha": data["id"], "branch": branch_name}


async def create_fix_mr(
    project_id: str | int,
    branch_name: str,
    incident_id: int,
    title: str,
    description: str,
    target_branch: str = "main",
) -> dict:
    """Open a Merge Request for the auto-fix branch."""
    pid = _encode_project(project_id)
    payload = {
        "source_branch": branch_name,
        "target_branch": target_branch,
        "title": title,
        "description": description,
        "labels": "opspilot-autofix,incident",
        "remove_source_branch": True,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_base()}/projects/{pid}/merge_requests",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("Auto-fix MR !%s created: %s", data["iid"], data["web_url"])
        return {
            "iid": data["iid"],
            "url": data["web_url"],
            "title": data["title"],
            "branch": branch_name,
        }


async def get_file_content(
    project_id: str | int,
    file_path: str,
    ref: str = "main",
) -> dict:
    """Get file content from GitLab repository."""
    pid = _encode_project(project_id)
    encoded_path = quote(file_path, safe="")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base()}/projects/{pid}/repository/files/{encoded_path}",
            params={"ref": ref},
            headers=_headers(),
        )
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        import base64
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return {"content": content, "sha": data["blob_id"]}


async def get_latest_commit_sha(
    project_id: str | int,
    ref: str = "main",
) -> str:
    """Get the latest commit SHA for a branch."""
    pid = _encode_project(project_id)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_base()}/projects/{pid}/repository/commits",
            params={"ref_name": ref, "per_page": 1},
            headers=_headers(),
        )
        resp.raise_for_status()
        commits = resp.json()
        if not commits:
            raise ValueError(f"No commits found on branch {ref}")
        return commits[0]["id"]
    
    async def create_fix_mr_workflow(
    project_id: str | int,
    filename: str,
    fixed_content: str,
    commit_message: str,
    description: str,
    incident_id: int,
) -> str:

    base_sha = await get_latest_commit_sha(project_id)

    branch_name = await create_fix_branch(
        project_id,
        incident_id,
        base_sha,
    )

    await commit_fix(
        project_id,
        branch_name,
        incident_id,
        filename,
        fixed_content,
        commit_message,
    )

    mr = await create_fix_mr(
        project_id=project_id,
        branch_name=branch_name,
        incident_id=incident_id,
        title=f"OpsPilot Auto Fix #{incident_id}",
        description=description,
    )

    return mr["url"]