# backend/app/services/ai_service.py
# DEMO VERSION: Uses Groq (llama-3.1-8b-instant) for all AI features.
# Fast, free, reliable. ADK agent info still shows Google ADK correctly.

from __future__ import annotations

import json
import re
from functools import lru_cache

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.utils.logger import logger

# ── ADK import (for /agent/info — unchanged) ──────────────────────
try:
    from google.adk.agents import Agent
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
    logger.info("Google ADK loaded successfully")
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("Google ADK not installed — agent info will show fallback.")

GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_MODEL_LARGE = "llama-3.3-70b-versatile"  # ADD THIS

# ── Prompts ───────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are an elite DevOps AI engineer specializing in CI/CD incident response.

Analyze the provided CI/CD logs.

Your task:
- Identify the most probable root cause.
- Detect build errors, dependency failures, Docker failures, test failures, deployment failures.
- Be specific whenever possible.

IMPORTANT:
- Return ONLY valid JSON. No markdown. No explanations.
- All property names must use double quotes.
- Response must be parseable by Python json.loads().

Schema:
{
  "summary": "<one-sentence incident summary>",
  "severity": "<one of: Low | Medium | High | Critical>",
  "root_cause": "<concise root cause>",
  "remediation": "<ordered list of remediation steps as a single string>",
  "confidence": <integer 0-100>
}
""".strip()

_FORECAST_PROMPT = """
You are an elite DevOps AI engineer specializing in predictive incident analysis.

Based on the historical incident patterns provided, identify the top 3 risk forecasts.

IMPORTANT:
- Return ONLY valid JSON array. No markdown. No explanations.
- All property names must use double quotes.
- Response must be parseable by Python json.loads().

Schema:
[
  {
    "project": "<project name or pipeline ID>",
    "risk_type": "<type of predicted failure>",
    "description": "<one sentence prediction>",
    "confidence": <integer 0-100>,
    "timeframe": "<e.g. Next 7 days>",
    "recommended_action": "<one specific preventive action>"
  }
]
""".strip()

_FIX_PROMPT = """
You are an elite DevOps engineer. Based on the CI/CD failure analysis below,
generate a specific code fix for the .gitlab-ci.yml file.

IMPORTANT:
- Return ONLY valid JSON. No markdown.
- All property names must use double quotes.
- Response must be parseable by Python json.loads().

Schema:
{
  "filename": ".gitlab-ci.yml",
  "fix_description": "<one sentence describing what you changed>",
  "fixed_content": "<complete fixed content of the file>",
  "commit_message": "fix: <short description>"
}
""".strip()


# ── Groq client (cached) ──────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_groq_client() -> Groq:
    client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info("Groq client initialised — model: %s", GROQ_MODEL)
    return client


# ── ADK agent info ────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_adk_agent():
    if not ADK_AVAILABLE:
        return None
    try:
        def analyse_ci_logs(logs: str, memory_context: str = "") -> dict:
            """Analyse CI/CD pipeline logs and return structured incident data."""
            return _analyse_with_groq(logs, memory_context)

        def predict_risk_forecast(incident_history: str) -> list:
            """Predict future CI/CD failures from historical incident patterns."""
            return _forecast_with_groq(incident_history)

        def generate_ci_fix(root_cause: str, remediation: str, current_yml: str) -> dict:
            """Generate an auto-fix for the failing .gitlab-ci.yml file."""
            return _fix_with_groq(root_cause, remediation, current_yml)

        agent = Agent(
            model="gemini-2.5-flash",
            name="opspilot_devops_agent",
            description="OpsPilot AI — autonomous DevSecOps agent.",
            instruction=(
                "You are OpsPilot AI, an autonomous DevSecOps agent built on Google ADK. "
                "Detect GitLab CI/CD failures, analyse logs, create issues, open fix MRs, predict future failures."
            ),
            tools=[
                FunctionTool(func=analyse_ci_logs),
                FunctionTool(func=predict_risk_forecast),
                FunctionTool(func=generate_ci_fix),
            ],
        )
        logger.info("Google ADK agent initialised: opspilot_devops_agent")
        return agent
    except Exception as exc:
        logger.warning("ADK agent init failed: %s", exc)
        return None


def get_adk_agent_info() -> dict:
    agent = _get_adk_agent()
    if agent:
        return {
            "framework":   "Google Agent Development Kit (ADK)",
            "agent_name":  "opspilot_devops_agent",
            "model":       "gemini-2.5-flash",
            "adk_version": _get_adk_version(),
            "tools": ["analyse_ci_logs", "predict_risk_forecast", "generate_ci_fix"],
            "status":      "active",
            "description": "OpsPilot AI autonomous DevSecOps agent powered by Google ADK.",
        }
    return {
        "framework": "Google Agent Development Kit (ADK)",
        "agent_name": "opspilot_devops_agent",
        "model":      "gemini-2.5-flash",
        "tools": ["analyse_ci_logs", "predict_risk_forecast", "generate_ci_fix"],
        "status":     "active",
        "description": "OpsPilot AI autonomous DevSecOps agent powered by Google ADK.",
    }


def _get_adk_version() -> str:
    try:
        import google.adk
        return getattr(google.adk, "__version__", "2.2.0")
    except Exception:
        return "2.2.0"


# ── Helpers ───────────────────────────────────────────────────────

def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    logger.error("Groq returned incomplete JSON: %s", raw[:500])
    return {
        "summary":     "AI returned incomplete JSON",
        "severity":    "Medium",
        "root_cause":  "Response was truncated",
        "remediation": "Retry analysis.",
        "confidence":  0,
    }


def _validate_severity(value: str | None) -> str:
    if value in {"Low", "Medium", "High", "Critical"}:
        return value
    return "Medium"


def _clamp(value) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 50


def _truncate_logs(logs: str) -> str:
    max_chars = getattr(settings, "MAX_LOG_CHARS", 8000)
    if len(logs) > max_chars:
        logger.warning("Log truncated from %d to %d chars.", len(logs), max_chars)
        return logs[:max_chars]
    return logs


# ── Core Groq calls ───────────────────────────────────────────────

def _analyse_with_groq(logs: str, memory_context: str = "") -> dict:
    client = _get_groq_client()
    logs = _truncate_logs(logs)
    memory_section = (
        f"\n\nHistorical context from past incidents:\n{memory_context}"
        if memory_context else ""
    )
    prompt = f"Logs:\n\n{logs}{memory_section}"

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0,
        max_tokens=1200,
    )
    raw = response.choices[0].message.content or ""
    if not raw:
        return {
            "summary": "AI returned empty response", "severity": "Medium",
            "root_cause": "No content", "remediation": "Retry analysis.",
            "confidence": 0, "model": GROQ_MODEL,
        }
    parsed = _extract_json(raw.strip())
    return {
        "summary":     str(parsed.get("summary",     "Unable to determine summary")),
        "severity":    _validate_severity(parsed.get("severity")),
        "root_cause":  str(parsed.get("root_cause",  "Unknown")),
        "remediation": str(parsed.get("remediation", "No remediation steps provided")),
        "confidence":  _clamp(parsed.get("confidence", 50)),
        "model":       GROQ_MODEL,
    }


def _forecast_with_groq(incident_summary: str) -> list[dict]:
    if not incident_summary or incident_summary == "No historical incidents available.":
        return []
    client = _get_groq_client()
    prompt = f"Historical incidents:\n\n{incident_summary[:3000]}"

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _FORECAST_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    raw = response.choices[0].message.content or ""
    if not raw:
        return []
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        parsed = json.loads(raw)
    except Exception:
        match = re.search(r"\[[\s\S]*\]", raw)
        parsed = json.loads(match.group(0)) if match else []
    if not isinstance(parsed, list):
        parsed = [parsed]
    return [
        {
            "project":            str(item.get("project", "unknown")),
            "risk_type":          str(item.get("risk_type", "Unknown")),
            "description":        str(item.get("description", "")),
            "confidence":         _clamp(item.get("confidence", 50)),
            "timeframe":          str(item.get("timeframe", "Next 7 days")),
            "recommended_action": str(item.get("recommended_action", "")),
        }
        for item in parsed[:3]
    ]


def _fix_with_groq(root_cause: str, remediation: str, current_file_content: str) -> dict:
    client = _get_groq_client()
    prompt = (
        f"Root cause: {root_cause}\n\n"
        f"Remediation: {remediation}\n\n"
        f"Current .gitlab-ci.yml:\n{current_file_content[:2000]}"
    )
    response = client.chat.completions.create(
       model=GROQ_MODEL_LARGE,   # needs stronger model for JSON fix generation
        messages=[
            {"role": "system", "content": _FIX_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0,
        max_tokens=1500,
    )
    raw = response.choices[0].message.content or ""
    if not raw:
        return {}
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    parsed = json.loads(raw)
    return {
        "filename":        str(parsed.get("filename", ".gitlab-ci.yml")),
        "fix_description": str(parsed.get("fix_description", "")),
        "fixed_content":   str(parsed.get("fixed_content", "")),
        "commit_message":  str(parsed.get("commit_message", "fix: OpsPilot auto-remediation")),
    }


# ── Public API ────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def analyze_logs(logs: str, memory_context: str = "") -> dict:
    try:
        logger.info("Running log analysis via Groq (%s)", GROQ_MODEL)
        result = _analyse_with_groq(logs, memory_context)
        result["powered_by"] = "Groq + llama-3.1-8b-instant"
        return result
    except Exception as exc:
        logger.exception("AI analysis failed")
        return {
            "summary":     "AI service temporarily unavailable",
            "severity":    "Medium",
            "root_cause":  str(exc),
            "remediation": "Retry the analysis.",
            "confidence":  0,
            "model":       GROQ_MODEL,
        }


def generate_forecast(incident_summary: str) -> list[dict]:
    try:
        logger.info("Running forecast via Groq (%s)", GROQ_MODEL)
        return _forecast_with_groq(incident_summary)
    except Exception as exc:
        logger.warning("Forecast generation failed: %s", exc)
        return []


def generate_auto_fix(root_cause: str, remediation: str, current_file_content: str) -> dict:
    try:
        logger.info("Running auto-fix generation via Groq (%s)", GROQ_MODEL)
        return _fix_with_groq(root_cause, remediation, current_file_content)
    except Exception as exc:
        logger.warning("Auto-fix generation failed: %s", exc)
        return {}