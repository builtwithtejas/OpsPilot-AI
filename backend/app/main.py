# backend/app/main.py

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
    retry_exception_handler,
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
    # Schema is managed by Alembic migrations (alembic upgrade head).
    # Uncomment the block below ONLY for local dev without Alembic:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type"],
)


# ── Rate limiting ─────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Exception handlers ────────────────────────────────────────────
app.add_exception_handler(RetryError, retry_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Routes ────────────────────────────────────────────────────────
app.include_router(api_router)


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