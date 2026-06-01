from __future__ import annotations

import json
import re

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.utils.logger import logger


# ── Prompts (module-level constants) ─────────────────────────────

_SYSTEM_PROMPT = """
You are an elite DevOps AI engineer specializing in CI/CD incident response.

Analyze the provided CI/CD logs.

Your task:
- Identify the most probable root cause.
- Detect build errors.
- Detect dependency failures.
- Detect Docker failures.
- Detect Kubernetes failures.
- Detect test failures.
- Detect deployment failures.
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

def _get_model():
    """Fresh configure every call — picks up new GEMINI_API_KEY without restart."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    logger.info("Using Gemini model: %s", settings.GEMINI_MODEL)
    return genai.GenerativeModel(model_name=settings.GEMINI_MODEL)


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

    logger.error("Gemini returned incomplete JSON: %s", raw[:500])
    return {
        "summary":     "AI returned incomplete JSON",
        "severity":    "Medium",
        "root_cause":  "Gemini response was truncated before JSON completed",
        "remediation": "Retry analysis. Reduce log size or increase output token limits.",
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


# ── Core log analysis ─────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
)
def analyze_logs(logs: str, memory_context: str = "") -> dict:
    try:
        model = _get_model()

        MAX_LOG_CHARS = 2500
        logs = logs[:MAX_LOG_CHARS]

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
                max_output_tokens=800,
            ),
        )

        raw = getattr(response, "text", "") or ""

        if not raw:
            logger.error("Gemini returned empty response")
            return {
                "summary":     "AI returned empty response",
                "severity":    "Medium",
                "root_cause":  "Gemini returned no content",
                "remediation": "Retry analysis.",
                "confidence":  0,
                "model":       settings.GEMINI_MODEL,
            }

        raw = raw.strip()
        logger.info("Gemini raw response: %s", raw)

        try:
            parsed = _extract_json(raw)
        except Exception as exc:
            logger.error("Failed to parse Gemini JSON: %s | Raw=%s", exc, raw)
            return {
                "summary":     "AI response parsing failed",
                "severity":    "Medium",
                "root_cause":  "Gemini returned malformed JSON",
                "remediation": (
                    "Retry analysis. "
                    "If the issue persists, improve prompt constraints "
                    "or inspect Gemini raw output logs."
                ),
                "confidence":  0,
                "model":       settings.GEMINI_MODEL,
            }

        return {
            "summary":     str(parsed.get("summary",     "Unable to determine summary")),
            "severity":    _validate_severity(parsed.get("severity")),
            "root_cause":  str(parsed.get("root_cause",  "Unknown")),
            "remediation": str(parsed.get("remediation", "No remediation steps provided")),
            "confidence":  _clamp(parsed.get("confidence", 50)),
            "model":       settings.GEMINI_MODEL,
        }

    except Exception as exc:
        logger.exception("AI analysis failed")
        return {
            "summary":     "AI service temporarily unavailable",
            "severity":    "Medium",
            "root_cause":  str(exc),
            "remediation": (
                "Retry the analysis. "
                "If the issue persists, verify Gemini API credentials, "
                "quota limits, and service availability."
            ),
            "confidence":  0,
            "model":       settings.GEMINI_MODEL,
        }


# ── Predictive forecast ───────────────────────────────────────────

def generate_forecast(incident_summary: str) -> list[dict]:
    """Generate predictive risk forecasts from historical incident patterns."""
    try:
        if not incident_summary or incident_summary == "No historical incidents available.":
            return []

        model = _get_model()
        prompt = f"{_FORECAST_PROMPT}\n\nHistorical incidents:\n\n{incident_summary[:3000]}"

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
                max_output_tokens=1000,
            ),
        )

        raw = getattr(response, "text", "") or ""
        if not raw:
            return []

        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
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

    except Exception as exc:
        logger.warning("Forecast generation failed: %s", exc)
        return []


# ── Auto-fix generation ───────────────────────────────────────────

def generate_auto_fix(
    root_cause: str,
    remediation: str,
    current_file_content: str,
) -> dict:
    """Generate a Gemini-powered auto-fix for the failing CI file."""
    try:
        model = _get_model()
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
    except Exception as exc:
        logger.warning("Auto-fix generation failed: %s", exc)
        return {}