# backend/app/api/routes/auth.py
#
# FIX (H-1): POST /auth/token now has its own tight rate limit of 10 req/min.
# The global limiter is 200/min — far too loose for an endpoint that exchanges
# a master secret for tokens. An attacker who guessed the key could hammer it
# freely. The per-route decorator overrides the global limit for this endpoint.
#
# Usage:
#   curl -X POST http://localhost:8000/auth/token \
#        -H "X-API-Key: your-master-key"
#
# Response:
#   { "access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600 }

from fastapi import APIRouter, Depends, Request
from app.core.security import create_access_token, require_master_key
from app.core.config import settings
from app.core.limiter import limiter  # reuse the app-level limiter instance

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", summary="Issue a short-lived JWT access token")
@limiter.limit("10/minute")   # FIX H-1: tight limit — brute-force protection
async def issue_token(
    request: Request,          # required by slowapi to extract the key
    _: str = Depends(require_master_key),
):
    token = create_access_token()
    expire_minutes = getattr(settings, "TOKEN_EXPIRE_MINUTES", 60)
    return {
        "access_token": token,
        "token_type":   "bearer",
        "expires_in":   expire_minutes * 60,   # seconds
    }