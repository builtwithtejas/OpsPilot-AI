from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from slowapi.errors import RateLimitExceeded
from tenacity import RetryError

from app.api.router import api_router
from app.core.config import settings
from app.core.limiter import limiter
from app.database.database import engine, Base
from app.middleware.error_handler import (
    unhandled_exception_handler,
    retry_exception_handler,
)
from app.models import incident, deployment, audit_log  # noqa: F401
from app.models.monitored_project import MonitoredProject  # noqa: F401
from app.utils.logger import logger
from slowapi import _rate_limit_exceeded_handler


@asynccontextmanager
async def lifespan(app):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Database tables verified")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered DevOps Incident Intelligence — Powered by Google Gemini & GitLab MCP",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app",  # covers all Vercel preview deploys
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RetryError, retry_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "ai_model": "Google Gemini 2.5 Flash",
        "agent": "GitLab MCP + Agent Orchestrator",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)