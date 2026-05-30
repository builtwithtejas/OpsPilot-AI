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

Analyze the provided logs.

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


@lru_cache(maxsize=1)
def _get_model():
    genai.configure(api_key=settings.GEMINI_API_KEY)

    logger.info("Using Gemini model: %s", settings.GEMINI_MODEL)

    return genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL
    )

def _extract_json(raw: str) -> dict:
    """
    Makes Gemini responses much more reliable.
    Handles:
    - markdown fences
    - extra text before/after JSON
    - malformed wrapper text
    """

    raw = raw.strip()

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)

    if match:
        return json.loads(match.group())

    raise ValueError("No valid JSON object found in Gemini response")


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
)
def analyze_logs(logs: str) -> dict:
    try:
        model = _get_model()

        prompt = f"{_SYSTEM_PROMPT}\n\nLogs:\n\n{logs}"

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
                max_output_tokens=800,
            ),
        )

        raw = response.text.strip()
        logger.info("Gemini raw response: %s", raw)

        try:
            parsed = _extract_json(raw)

        except Exception as exc:
            logger.error(
                "Failed to parse Gemini JSON: %s | Raw=%s",
                exc,
                raw,
            )

            return {
                "summary": "AI response parsing failed",
                "severity": "Medium",
                "root_cause": "Gemini returned malformed JSON",
                "remediation": (
                    "Retry analysis. "
                    "If the issue persists, improve prompt constraints "
                    "or inspect Gemini raw output logs."
                ),
                "confidence": 0,
                "model": settings.GEMINI_MODEL,
            }

        return {
            "summary": str(
                parsed.get(
                    "summary",
                    "Unable to determine summary",
                )
            ),
            "severity": _validate_severity(
                parsed.get("severity")
            ),
            "root_cause": str(
                parsed.get(
                    "root_cause",
                    "Unknown",
                )
            ),
            "remediation": str(
                parsed.get(
                    "remediation",
                    "No remediation steps provided",
                )
            ),
            "confidence": _clamp(
                parsed.get(
                    "confidence",
                    50,
                )
            ),
            "model": settings.GEMINI_MODEL,
        }

    except Exception as exc:
        logger.exception("AI analysis failed")

        return {
            "summary": "AI service temporarily unavailable",
            "severity": "Medium",
            "root_cause": str(exc),
            "remediation": (
                "Retry the analysis. "
                "If the issue persists, verify Gemini API credentials, "
                "quota limits, and service availability."
            ),
            "confidence": 0,
            "model": settings.GEMINI_MODEL,
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