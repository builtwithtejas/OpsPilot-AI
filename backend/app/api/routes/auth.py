# backend/app/api/routes/auth.py  (new file)
# Provides the token endpoint. Register this in router.py.
#
# Usage:
#   curl -X POST http://localhost:8000/auth/token \
#        -H "X-API-Key: your-master-key"
#
# Response:
#   { "access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600 }
#
# Then use the token for all other requests:
#   curl http://localhost:8000/incidents/ \
#        -H "Authorization: Bearer eyJ..."

from fastapi import APIRouter, Depends
from app.core.security import create_access_token, require_master_key
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", summary="Issue a short-lived JWT access token")
async def issue_token(_: str = Depends(require_master_key)):
    token = create_access_token()
    expire_minutes = getattr(settings, "TOKEN_EXPIRE_MINUTES", 60)
    return {
        "access_token": token,
        "token_type":   "bearer",
        "expires_in":   expire_minutes * 60,   # seconds
    }
