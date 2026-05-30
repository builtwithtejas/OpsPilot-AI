from __future__ import annotations

import json
import re

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


def _get_model():
    """Always configure fresh — picks up any new GEMINI_API_KEY without restart."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash-lite",
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=800,
        ),
    )


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def analyze_logs(logs: str) -> dict:
    try:
        model = _get_model()
        prompt = f"{_SYSTEM_PROMPT}\n\nLogs:\n\n{logs}"
        response = model.generate_content(prompt)
        raw = response.text.strip()

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

        return {
            "summary":     str(parsed.get("summary", "Unable to determine summary")),
            "severity":    _validate_severity(parsed.get("severity")),
            "root_cause":  str(parsed.get("root_cause", "Unknown")),
            "remediation": str(parsed.get("remediation", "No remediation steps provided")),
            "confidence":  _clamp(parsed.get("confidence", 50)),
            "model":       "gemini-2.0-flash-lite",
        }

    except Exception as exc:
        logger.error("AI analysis failed: %s", exc)
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