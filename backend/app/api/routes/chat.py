from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import google.generativeai as genai

from app.core.config import settings
from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.services.incident_service import get_incident_by_id
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"], dependencies=[Depends(require_api_key)])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    incident_id: int
    messages: list[ChatMessage]


@router.post("/stream", summary="AI chat about an incident — streams token by token")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    incident = get_incident_by_id(db, request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    system_prompt = f"""You are OpsPilot AI, an expert DevOps engineer helping investigate a CI/CD incident.

Incident context:
- ID: #{incident.id}
- Title: {incident.title}
- Severity: {incident.severity}
- Status: {incident.status}
- Description: {incident.description}
- Remediation: {incident.remediation}
- AI Confidence: {incident.confidence}%

Answer questions concisely and technically. Suggest exact commands and fixes."""

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
         model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=800),
    )

    # Build conversation history for Gemini
    history = []
    messages = list(request.messages)
    # Last message is the new user query — rest is history
    for msg in messages[:-1]:
        role = "user" if msg.role == "user" else "model"
        history.append({"role": role, "parts": [msg.content]})

    last_message = messages[-1].content if messages else ""

    async def token_generator():
        try:
            chat = model.start_chat(history=history)
            response = chat.send_message(last_message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            logger.error("Chat stream error: %s", exc)
            yield f"\n\n[Error: {str(exc)}]"

    return StreamingResponse(token_generator(), media_type="text/plain")