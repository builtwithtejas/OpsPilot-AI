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
    role: str       # "user" | "assistant" (mapped to "model" for Gemini)
    content: str


class ChatRequest(BaseModel):
    incident_id: int
    messages: list[ChatMessage]


@router.post("/stream", summary="Gemini-powered streaming AI chat about an incident")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    incident = get_incident_by_id(db, request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    system_prompt = f"""You are OpsPilot AI, an expert DevOps engineer powered by Google Gemini.
You are helping investigate the following CI/CD incident:

- ID: #{incident.id}
- Title: {incident.title}
- Severity: {incident.severity}
- Status: {incident.status}
- Description: {incident.description}
- Remediation: {incident.remediation}
- Confidence: {incident.confidence}%

Answer questions concisely and technically. Suggest commands, fixes, and next steps.
Always stay focused on this incident and DevOps topics."""

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=800),
    )

    # Build history in Gemini format (role must be "user" or "model")
    history = []
    for msg in request.messages[:-1]:   # all but last
        history.append({
            "role": "model" if msg.role == "assistant" else "user",
            "parts": [msg.content],
        })

    last_user_msg = request.messages[-1].content if request.messages else ""

    async def token_generator():
        try:
            chat = model.start_chat(history=history)
            response = chat.send_message(last_user_msg, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            logger.error("Gemini chat stream error: %s", exc)
            yield f"\n\n[Error: {str(exc)}]"

    return StreamingResponse(token_generator(), media_type="text/plain")
