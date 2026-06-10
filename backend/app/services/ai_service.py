# backend/app/services/ai_service.py
# DEMO MODE: Groq (llama-3.3-70b-versatile) replaces Gemini for all AI calls.
# Groq has a generous free tier with no quota exhaustion during demos.
# To revert: set USE_GROQ=false in .env (or remove it) — the original Gemini
# paths are preserved below and will be used automatically.
#
# .env additions needed:
#   GROQ_API_KEY=gsk_...
#   USE_GROQ=true           # set to false to revert to Gemini

from __future__ import annotations

import json
import re
from functools import lru_cache

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.utils.logger import logger

# ── Groq client (lazy import — only used when USE_GROQ=true) ─────
def _get_groq_client():
    try:
        from groq import Groq
        return Groq(api_key=settings.GROQ_API_KEY)
    except ImportError:
        raise RuntimeError("groq package not installed. Run: pip install groq")


# ── Gemini (used when USE_GROQ=false) ────────────────────────────
import google.generativeai as genai

@lru_cache(maxsize=4)
def _get_cached_gemini_model(api_key: str, model_name: str):
    genai.configure(api_key=api_key)
    logger.info("Gemini model configured: %s", model_name)
    return genai.GenerativeModel(model_name=model_name)

def _get_gemini_model():
    return _get_cached_gemini_model(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)


# ── Google ADK (optional — used when available + Gemini mode) ────
try:
    from google.adk.agents import Agent
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
    logger.info("Google ADK loaded successfully")
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("Google ADK not installed -- falling back to direct Gemini/Groq.")


# ── Prompts ───────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are an elite DevOps AI engineer specializing in CI/CD incident response.

Analyze the provided CI/CD logs.

Your task:
- Identify the most probable root cause.
- Detect build errors, dependency failures, Docker failures,
  Kubernetes failures, test failures, and deployment failures.
- Be specific whenever possible.

IMPORTANT:
- Return ONLY valid JSON.
- Do not wrap JSON in markdown.
- Do not add explanations.
- All property names must use double quotes.
- The response must be parseable by Python json.loads().

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
- Return ONLY valid JSON array.
- Do not wrap in markdown.
- Do not add explanations.
- All property names must use double quotes.
- Response must be parseable by Python json.loads().

Schema:
[
  {
    "project": "<project name or pipeline ID>",
    "risk_type": "<type of predicted failure e.g. Dependency failure, Docker failure>",
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
- Return ONLY valid JSON.
- Do not wrap in markdown.
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
    logger.error("AI returned incomplete JSON: %s", raw[:500])
    return {
        "summary":     "AI returned incomplete JSON",
        "severity":    "Medium",
        "root_cause":  "AI response was truncated before JSON completed",
        "remediation": "Retry analysis. Reduce log size or increase output token limits.",
        "confidence":  0,
    }


def _validate_severity(value: str | None) -> str:
    return value if value in {"Low", "Medium", "High", "Critical"} else "Medium"


def _clamp(value) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 50


def _truncate_logs(logs: str) -> str:
    max_chars = getattr(settings, "MAX_LOG_CHARS", 8000)
    if len(logs) > max_chars:
        logger.warning(
            "Log truncated from %d to %d chars. Set MAX_LOG_CHARS in .env to increase.",
            len(logs), max_chars,
        )
        return logs[:max_chars]
    return logs


def _active_model_name() -> str:
    """Return a human-readable model name for logging/responses."""
    if getattr(settings, "USE_GROQ", False):
        return getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
    return settings.GEMINI_MODEL


# ── Groq inference ────────────────────────────────────────────────

def _call_groq(system: str, user: str, max_tokens: int = 1200) -> str:
    client = _get_groq_client()
    model  = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
    logger.info("Calling Groq model: %s", model)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0,
        max_tokens=max_tokens,
        # Ask for JSON — Groq supports response_format for some models
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or ""


def _call_groq_array(system: str, user: str, max_tokens: int = 3000) -> str:
    """Separate helper for array responses -- Groq json_object mode requires an object root,
    so we wrap the instruction to return the array inside an object and unwrap it."""
    client = _get_groq_client()
    model  = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
    logger.info("Calling Groq model (array): %s", model)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system + "\n\nWrap the array in: {\"forecasts\": [...]}"},
            {"role": "user",   "content": user},
        ],
        temperature=0,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or ""


# ── Core analysis ─────────────────────────────────────────────────

def _analyse_with_groq(logs: str, memory_context: str = "") -> dict:
    logs = _truncate_logs(logs)
    memory_section = (
        f"\n\nHistorical context from past incidents:\n{memory_context}"
        if memory_context else ""
    )
    user = f"Logs:\n\n{logs}{memory_section}"
    raw  = _call_groq(_SYSTEM_PROMPT, user, max_tokens=1200)
    parsed = _extract_json(raw)
    return {
        "summary":     str(parsed.get("summary",     "Unable to determine summary")),
        "severity":    _validate_severity(parsed.get("severity")),
        "root_cause":  str(parsed.get("root_cause",  "Unknown")),
        "remediation": str(parsed.get("remediation", "No remediation steps provided")),
        "confidence":  _clamp(parsed.get("confidence", 50)),
        "model":       _active_model_name(),
        "powered_by":  "Groq · llama-3.3-70b-versatile",
    }


def _analyse_with_gemini(logs: str, memory_context: str = "") -> dict:
    model = _get_gemini_model()
    logs  = _truncate_logs(logs)
    memory_section = (
        f"\n\nHistorical context from past incidents:\n{memory_context}"
        if memory_context else ""
    )
    prompt = f"{_SYSTEM_PROMPT}\n\nLogs:\n\n{logs}{memory_section}"
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
            max_output_tokens=1200,
        ),
    )
    raw = getattr(response, "text", "") or ""
    if not raw:
        return {
            "summary": "AI returned empty response", "severity": "Medium",
            "root_cause": "Gemini returned no content", "remediation": "Retry analysis.",
            "confidence": 0, "model": settings.GEMINI_MODEL,
        }
    parsed = _extract_json(raw.strip())
    return {
        "summary":     str(parsed.get("summary",     "Unable to determine summary")),
        "severity":    _validate_severity(parsed.get("severity")),
        "root_cause":  str(parsed.get("root_cause",  "Unknown")),
        "remediation": str(parsed.get("remediation", "No remediation steps provided")),
        "confidence":  _clamp(parsed.get("confidence", 50)),
        "model":       settings.GEMINI_MODEL,
        "powered_by":  "Google Gemini",
    }


# ── Core forecast ─────────────────────────────────────────────────

def _forecast_with_groq(incident_summary: str) -> list[dict]:
    if not incident_summary or incident_summary == "No historical incidents available.":
        return []
    raw    = _call_groq_array(_FORECAST_PROMPT, f"Historical incidents:\n\n{incident_summary[:3000]}", max_tokens=2000)
    logger.info("Groq forecast raw: %s", raw[:300])
    parsed_obj = _extract_json(raw)
    parsed     = parsed_obj.get("forecasts", parsed_obj) if isinstance(parsed_obj, dict) else parsed_obj
    if not isinstance(parsed, list):
        parsed = [parsed]
    return [
        {
            "project":            str(item.get("project",            "unknown")),
            "risk_type":          str(item.get("risk_type",          "Unknown")),
            "description":        str(item.get("description",        "")),
            "confidence":         _clamp(item.get("confidence",       50)),
            "timeframe":          str(item.get("timeframe",          "Next 7 days")),
            "recommended_action": str(item.get("recommended_action", "")),
        }
        for item in parsed[:3]
    ]


def _forecast_with_gemini(incident_summary: str) -> list[dict]:
    logger.info("========== FORECAST START (Gemini) ==========")
    if not incident_summary or incident_summary == "No historical incidents available.":
        return []
    model  = _get_gemini_model()
    prompt = (
        f"{_FORECAST_PROMPT}\n\nReturn EXACTLY 3 forecast objects.\n"
        f"Return a COMPLETE valid JSON array.\n\n"
        f"Historical incidents:\n\n{incident_summary[:3000]}"
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
            max_output_tokens=3000,
        ),
    )
    raw = getattr(response, "text", "") or ""
    if not raw:
        return []
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        parsed = json.loads(raw)
    except Exception:
        match = re.search(r"\[[\s\S]*", raw)
        if not match:
            return []
        recovered = match.group(0)
        if not recovered.rstrip().endswith("]"):
            recovered += "]"
        try:
            parsed = json.loads(recovered)
        except Exception:
            return []
    if not isinstance(parsed, list):
        parsed = [parsed]
    return [
        {
            "project":            str(item.get("project",            "unknown")),
            "risk_type":          str(item.get("risk_type",          "Unknown")),
            "description":        str(item.get("description",        "")),
            "confidence":         _clamp(item.get("confidence",       50)),
            "timeframe":          str(item.get("timeframe",          "Next 7 days")),
            "recommended_action": str(item.get("recommended_action", "")),
        }
        for item in parsed[:3]
    ]


# ── Core auto-fix ─────────────────────────────────────────────────

def _fix_with_groq(root_cause: str, remediation: str, current_file_content: str) -> dict:
    user = (
        f"Root cause: {root_cause}\n\n"
        f"Remediation: {remediation}\n\n"
        f"Current .gitlab-ci.yml:\n{current_file_content[:2000]}"
    )
    raw    = _call_groq(_FIX_PROMPT, user, max_tokens=1500)
    parsed = _extract_json(raw)
    return {
        "filename":        str(parsed.get("filename",        ".gitlab-ci.yml")),
        "fix_description": str(parsed.get("fix_description", "")),
        "fixed_content":   str(parsed.get("fixed_content",   "")),
        "commit_message":  str(parsed.get("commit_message",  "fix: OpsPilot auto-remediation")),
    }


def _fix_with_gemini(root_cause: str, remediation: str, current_file_content: str) -> dict:
    model  = _get_gemini_model()
    prompt = (
        f"{_FIX_PROMPT}\n\n"
        f"Root cause: {root_cause}\n\n"
        f"Remediation: {remediation}\n\n"
        f"Current .gitlab-ci.yml:\n{current_file_content[:2000]}"
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
            max_output_tokens=1500,
        ),
    )
    raw = getattr(response, "text", "") or ""
    if not raw:
        return {}
    raw    = raw.strip()
    raw    = re.sub(r"^```(?:json)?\s*", "", raw)
    raw    = re.sub(r"\s*```$", "", raw)
    parsed = json.loads(raw)
    return {
        "filename":        str(parsed.get("filename",        ".gitlab-ci.yml")),
        "fix_description": str(parsed.get("fix_description", "")),
        "fixed_content":   str(parsed.get("fixed_content",   "")),
        "commit_message":  str(parsed.get("commit_message",  "fix: OpsPilot auto-remediation")),
    }


# ── Router — picks Groq or Gemini based on USE_GROQ setting ──────

def _use_groq() -> bool:
    return bool(getattr(settings, "USE_GROQ", False))


# ── ADK agent metadata (Gemini-only feature) ─────────────────────

@lru_cache(maxsize=1)
def _get_adk_agent():
    if not ADK_AVAILABLE or _use_groq():
        return None
    try:
        def analyse_ci_logs(logs: str, memory_context: str = "") -> dict:
            return _analyse_with_gemini(logs, memory_context)
        def predict_risk_forecast(incident_history: str) -> list:
            return _forecast_with_gemini(incident_history)
        def generate_ci_fix(root_cause: str, remediation: str, current_yml: str) -> dict:
            return _fix_with_gemini(root_cause, remediation, current_yml)

        agent = Agent(
            model=settings.GEMINI_MODEL,
            name="opspilot_devops_agent",
            description="OpsPilot AI autonomous DevSecOps agent.",
            instruction=(
                "You are OpsPilot AI, an autonomous DevSecOps agent. "
                "Detect failed GitLab pipelines, analyse logs, create issues, open MRs, notify."
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
    if _use_groq():
        return {
            "framework":   "Groq (demo mode)",
            "model":       getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
            "status":      "active",
            "description": "Running on Groq for demo -- zero quota exhaustion.",
        }
    agent = _get_adk_agent()
    if agent:
        return {
            "framework":   "Google Agent Development Kit (ADK)",
            "agent_name":  "opspilot_devops_agent",
            "model":       settings.GEMINI_MODEL,
            "tools":       ["analyse_ci_logs", "predict_risk_forecast", "generate_ci_fix"],
            "status":      "active",
        }
    return {"framework": "Google Gemini Direct", "model": settings.GEMINI_MODEL, "status": "fallback"}


# ── Public API (called by agent_service.py) ───────────────────────

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def analyze_logs(logs: str, memory_context: str = "") -> dict:
    """Analyse CI/CD logs. Uses Groq when USE_GROQ=true, else Gemini/ADK."""
    try:
        if _use_groq():
            logger.info("analyze_logs → Groq")
            return _analyse_with_groq(logs, memory_context)

        agent = _get_adk_agent()
        if agent:
            logger.info("analyze_logs → Google ADK + Gemini")
        else:
            logger.info("analyze_logs → Gemini direct")
        return _analyse_with_gemini(logs, memory_context)

    except Exception as exc:
        logger.exception("AI analysis failed")
        return {
            "summary":     "AI service temporarily unavailable",
            "severity":    "Medium",
            "root_cause":  str(exc),
            "remediation": (
                "Retry the analysis. If the issue persists, check API credentials, "
                "quota limits, and service availability."
            ),
            "confidence":  0,
            "model":       _active_model_name(),
        }


def generate_forecast(incident_summary: str) -> list[dict]:
    """Generate predictive risk forecasts. Uses Groq when USE_GROQ=true."""
    try:
        if _use_groq():
            logger.info("generate_forecast → Groq")
            return _forecast_with_groq(incident_summary)
        logger.info("generate_forecast → Gemini")
        return _forecast_with_gemini(incident_summary)
    except Exception as exc:
        logger.warning("Forecast generation failed: %s", exc)
        return []


def generate_auto_fix(root_cause: str, remediation: str, current_file_content: str) -> dict:
    """Generate auto-fix. Uses Groq when USE_GROQ=true."""
    try:
        if _use_groq():
            logger.info("generate_auto_fix → Groq")
            return _fix_with_groq(root_cause, remediation, current_file_content)
        logger.info("generate_auto_fix → Gemini")
        return _fix_with_gemini(root_cause, remediation, current_file_content)
    except Exception as exc:
        logger.warning("Auto-fix generation failed: %s", exc)
        return {}