from __future__ import annotations

from functools import lru_cache
from datetime import datetime, timezone

from github import Github, GithubException
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.utils.logger import logger


@lru_cache(maxsize=1)
def _get_repo():
    client = Github(settings.GITHUB_TOKEN)
    return client.get_repo(settings.GITHUB_REPO)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def get_workflow_runs(limit: int = 10) -> list[dict]:
    try:
        repo = _get_repo()

        results = []
        workflow_runs = repo.get_workflow_runs()

        count = 0

        for run in workflow_runs:
            if count >= limit:
                break

            run_number = getattr(run, "run_number", None)
            if run_number is None:
                run_number = getattr(run, "id", 0)

            created_at = run.created_at

            if isinstance(created_at, datetime):
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                created_at_str = created_at.isoformat()
            else:
                created_at_str = str(created_at)

            results.append(
                {
                    "workflow": run.name or "Unknown Workflow",
                    "status": run.status or "unknown",
                    "conclusion": run.conclusion or "unknown",
                    "branch": run.head_branch or "unknown",
                    "commit": (run.head_sha or "")[:7] or "unknown",
                    "actor": run.actor.login if run.actor else "unknown",
                    "run_number": run_number,
                    "url": run.html_url or "",
                    "created_at": created_at_str,
                }
            )

            count += 1

        return results

    except GithubException as exc:
        logger.error("GitHub API error fetching workflow runs: %s", exc)
        return []

    except Exception as exc:
        logger.error("Unexpected error fetching workflow runs: %s", exc)
        return []


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def get_repo_stats() -> dict:
    try:
        repo = _get_repo()

        commits = repo.get_commits()

        latest_commit = None

        for commit in commits:
            latest_commit = commit
            break

        if latest_commit:
            last_commit_sha = latest_commit.sha[:7]
            last_commit_message = latest_commit.commit.message
        else:
            last_commit_sha = "unknown"
            last_commit_message = "No commits found"

        return {
            "name": repo.name,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "watchers": repo.subscribers_count,
            "default_branch": repo.default_branch,
            "last_commit": last_commit_sha,
            "last_commit_message": last_commit_message,
        }

    except GithubException as exc:
        logger.error("GitHub API error fetching repo stats: %s", exc)
        return {}

    except Exception as exc:
        logger.error("Unexpected error fetching repo stats: %s", exc)
        return {}


def build_analytics(runs: list[dict]) -> dict:
    success = 0
    failed = 0

    trend_map: dict[str, int] = {}
    deployment_map: dict[str, int] = {}

    critical = 0
    warning = 0
    healthy = 0

    for run in runs:
        created_at_raw: str = run.get("created_at", "")
        conclusion: str = run.get("conclusion") or "unknown"

        try:
            dt = datetime.fromisoformat(
                created_at_raw.replace("Z", "+00:00")
            )

            date = dt.strftime("%Y-%m-%d")
            hour = dt.strftime("%H:00")

        except (ValueError, AttributeError):
            date = "unknown"
            hour = "unknown"

        trend_map[date] = trend_map.get(date, 0) + 1
        deployment_map[hour] = deployment_map.get(hour, 0) + 1

        if conclusion == "success":
            success += 1
            healthy += 1

        elif conclusion == "failure":
            failed += 1
            critical += 1

        else:
            warning += 1

    incident_trends = [
        {"day": k, "incidents": v}
        for k, v in sorted(trend_map.items())
    ]

    deployment_activity = [
        {"time": k, "deployments": v}
        for k, v in sorted(deployment_map.items())
    ]

    severity_distribution = [
        {"name": "Healthy", "value": healthy},
        {"name": "Warning", "value": warning},
        {"name": "Critical", "value": critical},
    ]

    if failed > 0:
        suggested_commands = [
            "docker logs $(docker ps -lq)",
            "kubectl get pods --all-namespaces",
            "git log --oneline -10",
            "pip install -r requirements.txt",
            "npm install",
        ]
    else:
        suggested_commands = [
            "kubectl get pods",
            "docker ps",
            "git status",
        ]

    total = len(runs)

    success_rate = (
        round((success / total) * 100, 1)
        if total > 0
        else 0.0
    )

    analysis = (
        f"{failed} failed deployment(s) detected out of "
        f"{total} total runs ({success_rate}% success rate). "
        f"System health: {healthy} healthy, "
        f"{warning} warning, {critical} critical."
    )

    return {
        "analysis": analysis,
        "incident_trends": incident_trends,
        "deployment_activity": deployment_activity,
        "severity_distribution": severity_distribution,
        "suggested_commands": suggested_commands,
        "stats": {
            "success": success,
            "failed": failed,
            "total": total,
            "success_rate": success_rate,
        },
    }