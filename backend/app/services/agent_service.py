from __future__ import annotations

"""
OpsPilot Agent Orchestrator
----------------------------
This is the Agent Builder–style orchestration layer.
It implements a multi-step autonomous agent that:

  Step 1 — Detect:   Pull failed pipelines from GitLab
  Step 2 — Analyse:  Send logs to Gemini for structured incident analysis
  Step 3 — Record:   Persist incident to database
  Step 4 — Act:      Create GitLab issue + post MR comment with remediation
  Step 5 — Notify:   Send Slack + email alerts

This mirrors the Google Cloud Agent Builder agent lifecycle:
plan → use tool → observe result → plan next step → use tool → finish
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.incident_schema import IncidentCreate
from app.services.ai_service import analyze_logs
from app.services.audit_service import log_action
from app.services.gitlab_service import (
    create_gitlab_issue,
    get_failed_pipelines,
    get_pipeline_jobs,
    post_pipeline_comment,
)
from app.services.incident_service import create_incident
from app.services.notification_service import notify_all
from app.utils.logger import logger


@dataclass
class AgentStep:
    name: str
    status: str = "pending"      # pending | running | done | failed
    result: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class AgentRun:
    run_id: str
    project_id: str
    pipeline_id: int | None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    steps: list[AgentStep] = field(default_factory=list)
    incident_id: int | None = None
    gitlab_issue_url: str | None = None
    status: str = "running"


async def run_agent(db: Session, project_id: str, pipeline_id: int | None = None) -> AgentRun:
    """
    Main agent entry point.
    If pipeline_id is given, analyse that specific pipeline.
    If not, auto-detect the most recently failed pipeline.
    """
    import uuid
    run = AgentRun(
        run_id=str(uuid.uuid4())[:8],
        project_id=project_id,
        pipeline_id=pipeline_id,
    )

    logger.info("Agent run %s started for project %s", run.run_id, project_id)

    # ── Step 1: Detect ────────────────────────────────────────────
    step = AgentStep(name="detect_failed_pipeline")
    run.steps.append(step)
    step.status = "running"
    try:
        if pipeline_id:
            step.result = {"pipeline_id": pipeline_id, "source": "provided"}
        else:
            pipelines = await get_failed_pipelines(project_id, limit=1)
            if not pipelines:
                step.status = "done"
                step.result = {"message": "No failed pipelines found — system healthy."}
                run.status = "healthy"
                return run
            pipeline_id = pipelines[0]["id"]
            run.pipeline_id = pipeline_id
            step.result = pipelines[0]
        step.status = "done"
        logger.info("[%s] Step 1 done — pipeline #%s", run.run_id, pipeline_id)
    except Exception as exc:
        step.status = "failed"
        step.error = str(exc)
        run.status = "failed"
        logger.error("[%s] Step 1 failed: %s", run.run_id, exc)
        return run

    # ── Step 2: Gather job logs ───────────────────────────────────
    step2 = AgentStep(name="gather_job_logs")
    run.steps.append(step2)
    step2.status = "running"
    try:
        jobs = await get_pipeline_jobs(project_id, pipeline_id)
        failed_jobs = [j for j in jobs if j["status"] == "failed"]
        log_text = _build_log_text(run.steps[0].result, failed_jobs)
        step2.result = {"job_count": len(jobs), "failed_jobs": len(failed_jobs), "log_preview": log_text[:300]}
        step2.status = "done"
        logger.info("[%s] Step 2 done — %d failed jobs", run.run_id, len(failed_jobs))
    except Exception as exc:
        step2.status = "failed"
        step2.error = str(exc)
        # Non-fatal — use minimal log text
        log_text = f"Pipeline {pipeline_id} failed. Unable to retrieve detailed job logs: {exc}"
        step2.result = {"error": str(exc)}
        step2.status = "done"

    # ── Step 3: Gemini analysis ───────────────────────────────────
    step3 = AgentStep(name="gemini_analysis")
    run.steps.append(step3)
    step3.status = "running"
    try:
        analysis = analyze_logs(log_text)
        step3.result = analysis
        step3.status = "done"
        logger.info("[%s] Step 3 done — severity: %s, confidence: %s%%", run.run_id, analysis["severity"], analysis["confidence"])
    except Exception as exc:
        step3.status = "failed"
        step3.error = str(exc)
        run.status = "failed"
        logger.error("[%s] Step 3 failed: %s", run.run_id, exc)
        return run

    # ── Step 4: Record incident ───────────────────────────────────
    step4 = AgentStep(name="record_incident")
    run.steps.append(step4)
    step4.status = "running"
    try:
        incident = create_incident(
    db,
    IncidentCreate(
        title=f"[GitLab #{pipeline_id}] {analysis['summary'][:90]}",
        severity=analysis["severity"],
        status="Open",
        description=analysis["summary"],
        remediation=analysis["remediation"],
        confidence=analysis["confidence"],
        source="GitLab",
        pipeline_id=pipeline_id,
    ),
)
        log_action(db, incident.id, "created", f"Auto-created by OpsPilot agent (pipeline #{pipeline_id})", actor="agent")
        run.incident_id = incident.id
        step4.result = {"incident_id": incident.id}
        step4.status = "done"
        logger.info("[%s] Step 4 done — incident #%d", run.run_id, incident.id)
    except Exception as exc:
        step4.status = "failed"
        step4.error = str(exc)
        run.status = "failed"
        logger.error("[%s] Step 4 failed: %s", run.run_id, exc)
        return run

    # ── Step 5: Create GitLab issue + MR comment ─────────────────
    step5 = AgentStep(name="gitlab_action")
    run.steps.append(step5)
    step5.status = "running"
    try:
        issue_body = _build_issue_body(analysis, incident.id, run.run_id)
        issue = await create_gitlab_issue(
            project_id,
            title=f"🔴 OpsPilot: {analysis['severity']} — {analysis['summary'][:80]}",
            description=issue_body,
            labels=["opspilot", "incident", analysis["severity"].lower(), "ci-cd"],
        )
        run.gitlab_issue_url = issue["url"]
        incident.gitlab_issue_url = issue["url"]
        db.commit()

        # Also try to comment on any open MR
        try:
            mr_comment = _build_mr_comment(analysis, issue["url"])
            await post_pipeline_comment(project_id, pipeline_id, mr_comment)
        except Exception:
            pass  # MR comment is bonus — don't fail the whole run

        step5.result = {"issue_url": issue["url"], "issue_iid": issue["iid"]}
        step5.status = "done"
        logger.info("[%s] Step 5 done — GitLab issue: %s", run.run_id, issue["url"])
    except Exception as exc:
        step5.status = "failed"
        step5.error = str(exc)
        logger.warning("[%s] Step 5 failed (non-fatal): %s", run.run_id, exc)

    # ── Step 6: Notify ────────────────────────────────────────────
    step6 = AgentStep(name="notify")
    run.steps.append(step6)
    step6.status = "running"
    try:
        await notify_all(incident.id, incident.title, incident.severity, incident.description, incident.remediation)
        step6.result = {"slack": bool(settings.SLACK_WEBHOOK_URL), "email": bool(settings.SENDGRID_API_KEY)}
        step6.status = "done"
    except Exception as exc:
        step6.status = "failed"
        step6.error = str(exc)

    run.status = "completed"
    logger.info("[%s] Agent run complete — incident #%d, issue: %s", run.run_id, incident.id, run.gitlab_issue_url)
    return run


def _build_log_text(pipeline_info: dict, failed_jobs: list[dict]) -> str:
    lines = [
        f"Pipeline ID: {pipeline_info.get('id', 'unknown')}",
        f"Branch: {pipeline_info.get('ref', 'unknown')}",
        f"Commit: {pipeline_info.get('sha', 'unknown')}",
        f"Status: {pipeline_info.get('status', 'failed')}",
        f"URL: {pipeline_info.get('web_url', '')}",
        "",
        "Failed jobs:",
    ]
    for job in failed_jobs:
        lines.append(f"  - [{job['stage']}] {job['name']}: {job['status']} (reason: {job.get('failure_reason', 'unknown')})")
    return "\n".join(lines)


def _build_issue_body(analysis: dict, incident_id: int, run_id: str) -> str:
    return f"""## 🤖 OpsPilot AI — Automated Incident Report

**Run ID:** `{run_id}`  
**OpsPilot Incident:** #{incident_id}  
**AI Model:** Gemini 2.5 Flash
**Confidence:** {analysis['confidence']}%

---

### 📋 Summary
{analysis['summary']}

### 🔍 Root Cause
{analysis['root_cause']}

### 🛠 Remediation Steps
{analysis['remediation']}

---

*This issue was automatically created by [OpsPilot AI](https://opspilot.vercel.app) — AI-Powered CI/CD Incident Intelligence.*  
*Severity: **{analysis['severity']}** · Powered by Google Gemini*
"""


def _build_mr_comment(analysis: dict, issue_url: str) -> str:
    return f"""### 🤖 OpsPilot AI — Pipeline Failure Analysis

**Severity:** {analysis['severity']} | **Confidence:** {analysis['confidence']}%

**Root cause:** {analysis['root_cause']}

**Remediation:** {analysis['remediation'][:400]}

📋 Full incident report: {issue_url}

*Powered by OpsPilot AI × Google Gemini*"""
