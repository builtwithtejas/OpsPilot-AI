from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from tenacity import RetryError

from app.api.router import api_router
from app.core.config import settings
from app.database.database import Base, engine
from app.middleware.error_handler import (
    unhandled_exception_handler,
)
from app.models import incident, deployment, audit_log  # noqa: F401
from app.utils.logger import logger

# ── Rate limiter ──────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


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
origins = [
    "http://localhost:3000",
    "https://ops-pilot-ctpi4iwwf-tejas-projects10.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiting ─────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

# ── Global error handler ──────────────────────────────────────────
app.add_exception_handler(
    Exception,
    unhandled_exception_handler
)

# ── Routes ────────────────────────────────────────────────────────
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "ai_model": "Google Gemini 1.5 Flash",
        "agent": "GitLab MCP + Agent Orchestrator",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)