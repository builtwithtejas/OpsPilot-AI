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

api_router = APIRouter()
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
