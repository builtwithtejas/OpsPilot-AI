# backend/app/main.py
# FIX: Removed scattered router includes (now in router.py).
#      Registered the missing retry_exception_handler.
#      Tightened CORS — no more wildcard Vercel regex.
#      /health and root stay public; everything else is guarded by require_api_key in each router.

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from tenacity import RetryError

from app.api.router import api_router
from app.core.config import settings
from app.database.database import engine, Base
from app.middleware.error_handler import (
    unhandled_exception_handler,
    retry_exception_handler,           # FIX: was defined but never registered
)
from app.models import incident, deployment, audit_log  # noqa: F401
from app.utils.logger import logger
from app.models.monitored_project import MonitoredProject  # noqa: F401

# ── Rate limiter ──────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"]
)


# ── App lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # FIX: use async engine — run_sync wraps the sync create_all call
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)

    # Cleanly dispose the connection pool on shutdown
    await engine.dispose()


# ── FastAPI App ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered DevOps Incident Intelligence — Powered by Google Gemini & GitLab MCP",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Configuration ────────────────────────────────────────────
# FIX: replaced open Vercel wildcard with explicit allowed origins from settings.
# Set ALLOWED_ORIGINS in your .env, e.g.:
#   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
    expose_headers=["Content-Type"],
)


# ── Rate limiting ─────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Exception handlers ────────────────────────────────────────────
app.add_exception_handler(RetryError, retry_exception_handler)   # FIX: now registered
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Routes ────────────────────────────────────────────────────────
app.include_router(api_router)                                   # FIX: single include, all routers inside


# ── Root Endpoint ─────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "ai_model": "Google Gemini 2.5 Flash",
        "agent": "GitLab MCP + Agent Orchestrator",
    }


# ── Favicon ───────────────────────────────────────────────────────
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# ── Health Check (public — intentionally no auth) ─────────────────
@app.get("/health")
async def health():
    return {"status": "healthy"}
