from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
- Remediation steps: {incident.remediation}
- Confidence: {incident.confidence}%

Answer questions about this incident concisely and technically. Suggest commands, fixes, and next steps."""

    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    async def token_generator():
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
                max_tokens=800,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            logger.error("Chat stream error: %s", exc)
            yield f"\n\n[Error: {str(exc)}]"

    return StreamingResponse(token_generator(), media_type="text/plain")