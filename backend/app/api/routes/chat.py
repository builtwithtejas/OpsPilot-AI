# backend/app/api/routes/chat.py
# PRODUCTION VERSION: Gemini 2.5 Flash streaming chat.

from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import google.generativeai as genai

from app.core.security import require_api_key
from app.core.config import settings
from app.database.dependencies import get_db
from app.services.incident_service import get_incident_by_id
from app.services.ai_service import _get_cached_model
from app.utils.logger import logger

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


def _stream_chunks_sync(
    history: list[dict],
    last_message: str,
    system_prompt: str,
) -> list[str]:
    """Run Gemini streaming in a thread pool and collect all chunks."""
    # Reuse the cached configured model — no per-request reconfigure
    _get_cached_model(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)

    chat_model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=800,
        ),
    )
    chat = chat_model.start_chat(history=history)
    response = chat.send_message(last_message, stream=True)
    return [chunk.text for chunk in response if chunk.text]


@router.post("/stream", summary="AI chat about an incident — streams token by token")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    incident = await get_incident_by_id(db, request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    system_prompt = _build_system_prompt(incident)

    # Build Gemini history format
    history = []
    messages = list(request.messages)
    for msg in messages[:-1]:
        role = "user" if msg.role == "user" else "model"
        history.append({"role": role, "parts": [msg.content]})

    last_message = messages[-1].content if messages else ""

    async def token_generator():
        try:
            # Run blocking Gemini stream in thread pool — never blocks event loop
            chunks = await asyncio.to_thread(
                _stream_chunks_sync,
                history,
                last_message,
                system_prompt,
            )
            for chunk in chunks:
                yield chunk
        except Exception as exc:
            logger.error("Chat stream error: %s", exc)
            yield f"\n\n[Error: {str(exc)}]"

    return StreamingResponse(token_generator(), media_type="text/plain")