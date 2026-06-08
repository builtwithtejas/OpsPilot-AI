# backend/app/core/security.py
# FIX: Replaces single shared API key with short-lived JWT tokens.
#
# HOW IT WORKS:
#   1. Admin calls POST /auth/token with the master API_KEY in the header.
#   2. They get back a JWT valid for TOKEN_EXPIRE_MINUTES (default 60 mins).
#   3. All other routes use this JWT in the Authorization: Bearer <token> header.
#   4. Tokens expire automatically — no more permanent leaked keys.
#
# SETUP: Add to requirements.txt:
#   python-jose[cryptography]==3.3.0
#
# Add to .env:
#   JWT_SECRET_KEY=<random 64-char hex>   # python -c "import secrets; print(secrets.token_hex(32))"
#   TOKEN_EXPIRE_MINUTES=60

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError, jwt

from app.core.config import settings
from app.utils.logger import logger

# ── Master key guard (used only for /auth/token) ──────────────────
_master_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_master_key(api_key: str = Security(_master_key_header)) -> str:
    """Guards the token-issuance endpoint. Requires the raw API_KEY."""
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing master API key.",
        )
    return api_key


# ── JWT token issuance ────────────────────────────────────────────
def create_access_token(subject: str = "opspilot-client") -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=getattr(settings, "TOKEN_EXPIRE_MINUTES", 60)
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


# ── JWT token validation (used by all protected routes) ───────────
_bearer = HTTPBearer(auto_error=False)
# Also still support X-API-Key for backward compat during rollout
_legacy_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer),
    legacy_key: str | None                      = Security(_legacy_key_header),
) -> str:
    """
    Accepts either:
      - Authorization: Bearer <jwt>   (preferred)
      - X-API-Key: <master_key>       (legacy, still works during transition)
    """
    # Try JWT first
    if bearer and bearer.credentials:
        try:
            payload = jwt.decode(
                bearer.credentials,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"],
            )
            return payload.get("sub", "unknown")
        except JWTError as exc:
            logger.warning("JWT validation failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token. Request a new one via POST /auth/token.",
            )

    # Fall back to legacy X-API-Key (remove this block after full migration)
    if legacy_key and legacy_key == settings.API_KEY:
        logger.warning("X-API-Key used — migrate to JWT tokens.")
        return "legacy-client"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Pass Authorization: Bearer <token>.",
    )
