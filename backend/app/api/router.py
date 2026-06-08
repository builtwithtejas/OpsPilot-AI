# backend/app/api/router.py
# FIX: Registered the new auth router so POST /auth/token is accessible.

from fastapi import APIRouter
from app.api.routes import (
    agent,
    ai,
    chat,
    github_routes,
    gitlab_routes,
    health,
    incidents,
    logs,
    metrics,
    webhooks,
)
from app.api.routes.projects import router as projects_router
from app.api.routes.forecast import router as forecast_router
from app.api.routes.auth import router as auth_router       # FIX: new auth router

api_router = APIRouter()

api_router.include_router(auth_router)                      # FIX: token issuance endpoint
api_router.include_router(health.router)
api_router.include_router(ai.router)
api_router.include_router(chat.router)
api_router.include_router(agent.router)
api_router.include_router(incidents.router)
api_router.include_router(logs.router)
api_router.include_router(metrics.router)
api_router.include_router(github_routes.router)
api_router.include_router(gitlab_routes.router)
api_router.include_router(webhooks.router)
api_router.include_router(projects_router)
api_router.include_router(forecast_router)
