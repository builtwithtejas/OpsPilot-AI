from __future__ import annotations

"""
OpsPilot Agent Orchestrator
----------------------------
Multi-step autonomous agent mirroring Google Cloud Agent Builder lifecycle:
plan → use tool → observe result → plan next step → use tool → finish

  Step 1 — Detect:   Pull failed pipelines from GitLab
  Step 2 — Gather:   Fetch job logs and failure details
  Step 3 — Analyse:  Send logs to Gemini for structured incident analysis
  Step 4 — Record:   Persist incident to database
  Step 5 — Act:      Create GitLab issue + post MR comment
  Step 6 — Notify:   Send Slack + email alerts
  Step 7 — Duo:      Notify GitLab Duo Agent Platform
"""

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
    get_job_trace,
    get_pipeline_jobs,
    post_pipeline_comment,
    trigger_duo_agent,
)
from app.services.incident_service import create_incident
from app.services.notification_service import notify_all
from app.utils.logger import logger
from app.services.incident_service import create_incident, get_incident_by_pipeline_id, get_incidents_summary_for_memory

@dataclass
class AgentStep:
    name:   str
    status: str = "pending"
    result: dict = field(default_factory=dict)
    error:  str | None = None


@dataclass
class AgentRun:
    run_id:           str
    project_id:       str
    pipeline_id:      int | None
    started_at:       str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    steps:            list[AgentStep] = field(default_factory=list)
    incident_id:      int | None = None
    gitlab_issue_url: str | None = None
    status:           str = "running"


async def run_agent(
    db: Session,
    project_id: str,
    pipeline_id: int | None = None,
    triggered_by: str = "manual",
) -> AgentRun:
    import uuid
    run = AgentRun(
        run_id=str(uuid.uuid4())[:8],
        project_id=project_id,
        pipeline_id=pipeline_id,
    )
    logger.info("Agent run %s started for project %s", run.run_id, project_id)

    # ── Step 1: Detect ────────────────────────────────────────────
    step1 = AgentStep(name="detect_failed_pipeline")
    run.steps.append(step1)
    step1.status = "running"
    try:
        if pipeline_id:
            step1.result = {"pipeline_id": pipeline_id, "source": "provided"}
        else:
            pipelines = await get_failed_pipelines(project_id, limit=1)
            if not pipelines:
                step1.status = "done"
                step1.result = {"message": "No failed pipelines found — system healthy."}
                run.status = "healthy"
                return run
            pipeline_id = pipelines[0]["id"]
            run.pipeline_id = pipeline_id
            step1.result = pipelines[0]
        step1.status = "done"
        logger.info("[%s] Step 1 done — pipeline #%s", run.run_id, pipeline_id)
    except Exception as exc:
        step1.status = "failed"
        step1.error = str(exc)
        run.status = "failed"
        logger.error("[%s] Step 1 failed: %s", run.run_id, exc)
        return run

    # ── Step 2: Gather job logs ───────────────────────────────────
    step2 = AgentStep(name="gather_job_logs")
    run.steps.append(step2)
    step2.status = "running"
    log_text = ""
    try:
        jobs = await get_pipeline_jobs(project_id, pipeline_id)
        logger.info("[%s] Retrieved %d jobs", run.run_id, len(jobs))

        for job in jobs:
            logger.info("Job: id=%s name=%s status=%s", job.get("id"), job.get("name"), job.get("status"))

        failed_jobs = [j for j in jobs if j["status"] == "failed"]
        log_text = _build_log_text(step1.result, failed_jobs)

        # Fetch real job traces — cap at 1500 chars per job to avoid Gemini truncation
        for job in failed_jobs[:2]:
            try:
                trace = await get_job_trace(project_id, job["id"])
                # Take last 1500 chars — errors appear at the end
                log_text += f"\n\n===== JOB: {job['name']} =====\n{trace[-1500:]}"
            except Exception as te:
                logger.warning("Unable to fetch trace for job %s: %s", job["id"], te)

        step2.result = {
            "job_count":   len(jobs),
            "failed_jobs": len(failed_jobs),
            "log_preview": log_text[:300],
        }
        step2.status = "done"
        logger.info("[%s] Step 2 done — %d failed jobs, log_len=%d", run.run_id, len(failed_jobs), len(log_text))
    except Exception as exc:
        step2.status = "failed"
        step2.error = str(exc)
        log_text = f"Pipeline {pipeline_id} failed. Unable to retrieve detailed job logs: {exc}"
        step2.result = {"error": str(exc)}
        step2.status = "done"

    # ── Step 3: Gemini analysis ───────────────────────────────────
    step3 = AgentStep(name="gemini_analysis")
    run.steps.append(step3)
    step3.status = "running"
    try:
        memory_context = get_incidents_summary_for_memory(db)
        analysis = analyze_logs(log_text, memory_context=memory_context)
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
        incident = create_incident(db, IncidentCreate(
            title=f"[GitLab #{pipeline_id}] {analysis['summary'][:90]}",
            severity=analysis["severity"],
            status="Open",
            description=analysis["summary"],
            remediation=analysis["remediation"],
            confidence=analysis["confidence"],
            source="GitLab",
            pipeline_id=str(pipeline_id),    # ← FIX: cast int to str, Pydantic requires str
        ))
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

        # Update incident record with GitLab issue URL
        incident.gitlab_issue_url = issue["url"]
        db.commit()

        # Try MR comment — non-fatal
        try:
            await post_pipeline_comment(project_id, pipeline_id, _build_mr_comment(analysis, issue["url"]))
        except Exception:
            pass

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

    # ── Step 7: GitLab Duo Agent Platform ─────────────────────────
    step7 = AgentStep(name="duo_agent_platform")
    run.steps.append(step7)
    step7.status = "running"
    try:
        duo_result = await trigger_duo_agent(
            project_id=project_id,
            incident_summary=analysis["summary"],
            issue_url=run.gitlab_issue_url or "N/A",
        )
        step7.result = {
            **duo_result,
            "triggered_by": triggered_by,
            "agent_id": settings.GITLAB_AGENT_ID,
        }
        step7.status = "done"
        logger.info("[%s] Step 7 done — Duo agent notified", run.run_id)
    except Exception as exc:
        step7.status = "failed"
        step7.error = str(exc)
        logger.warning("[%s] Step 7 failed (non-fatal): %s", run.run_id, exc)

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

*Automatically created by OpsPilot AI — AI-Powered CI/CD Incident Intelligence.*
*Severity: **{analysis['severity']}** · Powered by Google Gemini 2.5 Flash × GitLab MCP*
"""


def _build_mr_comment(analysis: dict, issue_url: str) -> str:
    return f"""### 🤖 OpsPilot AI — Pipeline Failure Analysis

**Severity:** {analysis['severity']} | **Confidence:** {analysis['confidence']}%

**Root cause:** {analysis['root_cause']}

**Remediation:** {analysis['remediation'][:400]}

📋 Full incident report: {issue_url}

*Powered by OpsPilot AI × Google Gemini 2.5 Flash*"""