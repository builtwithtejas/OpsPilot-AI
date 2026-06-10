# C-6 FIX 1: genai is no longer reconfigured on every request.
#             The model instance is retrieved from the shared lru_cache in ai_service.py.
# C-6 FIX 2: The sync chunk iterator (for chunk in response) is moved into a
#             asyncio.to_thread() worker that collects all chunks and yields them,
#             so the async generator never blocks the event loop.

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.services.ai_service import _get_gemini_model
from app.core.config import settings
from app.services.incident_service import get_incident_by_id
from app.utils.logger import logger

import google.generativeai as genai

router = APIRouter(prefix="/chat", tags=["Chat"], dependencies=[Depends(require_api_key)])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    incident_id: int
    messages: list[ChatMessage]


def _build_system_prompt(incident) -> str:
    return (
        f"You are OpsPilot AI, an expert DevOps engineer helping investigate a CI/CD incident.\n\n"
        f"Incident context:\n"
        f"- ID: #{incident.id}\n"
        f"- Title: {incident.title}\n"
        f"- Severity: {incident.severity}\n"
        f"- Status: {incident.status}\n"
        f"- Description: {incident.description}\n"
        f"- Remediation: {incident.remediation}\n"
        f"- AI Confidence: {incident.confidence}%\n\n"
        f"Answer questions concisely and technically. Suggest exact commands and fixes."
    )


def _stream_chunks_sync(model, history: list, last_message: str, system_prompt: str) -> list[str]:
    """Run the sync Gemini streaming call and collect all text chunks."""
    # C-6 FIX: wrapping in to_thread — this entire function runs in a thread pool
    chat_model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=800),
    )
    # Reuse the already-configured genai (api key was set by _get_cached_model)
    chat = chat_model.start_chat(history=history)
    response = chat.send_message(last_message, stream=True)
    return [chunk.text for chunk in response if chunk.text]


@router.post("/stream", summary="AI chat about an incident — streams token by token")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    incident = await get_incident_by_id(db, request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    system_prompt = _build_system_prompt(incident)

    # C-6 FIX 1: Ensure genai is configured via the shared cache (no per-request reconfigure)
    _get_gemini_model(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)

    history = []
    messages = list(request.messages)
    for msg in messages[:-1]:
        role = "user" if msg.role == "user" else "model"
        history.append({"role": role, "parts": [msg.content]})

    last_message = messages[-1].content if messages else ""

    async def token_generator():
        try:
            # C-6 FIX 2: Run the blocking sync iterator entirely in a thread pool.
            # All chunks are collected there, then streamed back here without blocking.
            chunks = await asyncio.to_thread(
                _stream_chunks_sync, None, history, last_message, system_prompt
            )
            for chunk in chunks:
                yield chunk
        except Exception as exc:
            logger.error("Chat stream error: %s", exc)
            yield f"\n\n[Error: {str(exc)}]"

    return StreamingResponse(token_generator(), media_type="text/plain")
