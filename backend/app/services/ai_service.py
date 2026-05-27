from __future__ import annotations

import json
import re
from functools import lru_cache

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.utils.logger import logger

_SYSTEM_PROMPT = """
You are an elite DevOps AI engineer specializing in CI/CD incident response.

Analyze the provided logs and respond with ONLY a valid JSON object — no markdown, no preamble.

Schema:
{
  "summary": "<one-sentence incident summary>",
  "severity": "<one of: Low | Medium | High | Critical>",
  "root_cause": "<concise root cause>",
  "remediation": "<ordered list of remediation steps as a single string>",
  "confidence": <integer 0-100>
}
""".strip()


@lru_cache(maxsize=1)
def _get_model():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=800,
        ),
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_logs(logs: str) -> dict:
    """Call Gemini and return structured incident analysis."""
    try:
        model = _get_model()
        response = model.generate_content(f"Logs:\n\n{logs}")
        raw = response.text.strip()

        # Strip accidental markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

        return {
            "summary":     str(parsed.get("summary", "Unable to determine summary")),
            "severity":    _validate_severity(parsed.get("severity")),
            "root_cause":  str(parsed.get("root_cause", "Unknown")),
            "remediation": str(parsed.get("remediation", "No remediation steps provided")),
            "confidence":  _clamp(parsed.get("confidence", 50)),
            "model":       "gemini-1.5-flash",
        }

    except (json.JSONDecodeError, Exception) as exc:
        logger.error("Gemini analysis failed: %s", exc)
        raise


def _validate_severity(value: str | None) -> str:
    if value in {"Low", "Medium", "High", "Critical"}:
        return value
    return "Medium"


def _clamp(value) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 50
