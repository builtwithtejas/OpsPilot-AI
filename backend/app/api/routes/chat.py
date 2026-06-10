# backend/app/api/routes/chat.py
# DEMO VERSION: Switched from Gemini to Groq (llama-3.1-8b-instant) for chat streaming.
# Groq streams tokens extremely fast — looks great on camera.

from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.core.config import settings
from app.database.dependencies import get_db
from app.services.incident_service import get_incident_by_id
from app.utils.logger import logger

from groq import Groq

router = APIRouter(prefix="/chat", tags=["Chat"], dependencies=[Depends(require_api_key)])

GROQ_MODEL = "llama-3.1-8b-instant"


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
    messages: list[dict],
    system_prompt: str,
) -> list[str]:
    """Run Groq streaming in a thread pool and collect all chunks."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=0.3,
        max_tokens=800,
        stream=True,
    )

    chunks = []
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            chunks.append(delta)
    return chunks


@router.post("/stream", summary="AI chat about an incident — streams token by token")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    incident = await get_incident_by_id(db, request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    system_prompt = _build_system_prompt(incident)

    # Build message history for Groq
    groq_messages = []
    for msg in request.messages:
        role = "user" if msg.role == "user" else "assistant"
        groq_messages.append({"role": role, "content": msg.content})

    async def token_generator():
        try:
            # Run blocking Groq stream in thread pool — never blocks event loop
            chunks = await asyncio.to_thread(
                _stream_chunks_sync,
                groq_messages,
                system_prompt,
            )
            for chunk in chunks:
                yield chunk
        except Exception as exc:
            logger.error("Chat stream error: %s", exc)
            yield f"\n\n[Error: {str(exc)}]"

    return StreamingResponse(token_generator(), media_type="text/plain")
