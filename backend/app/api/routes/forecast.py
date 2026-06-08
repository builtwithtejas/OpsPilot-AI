# backend/app/api/routes/forecast.py
# FIX: Converted to async def, Session → AsyncSession, service calls awaited.

from __future__ import annotations

import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.database.dependencies import get_db
from app.services.incident_service import get_incidents_summary_for_memory
from app.services.ai_service import generate_forecast
from app.utils.logger import logger

router = APIRouter(prefix="/forecast", tags=["Forecast"])

# Simple in-memory cache — 6 hour TTL
_cache: dict = {"data": [], "ts": 0}
_TTL = 6 * 3600


@router.get("/", summary="Get predictive risk forecast based on incident history")
async def get_forecast(
    refresh: bool = False,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    global _cache

    now = time.time()
    if not refresh and _cache["data"] and (now - _cache["ts"]) < _TTL:
        logger.info("Forecast: returning cached result")
        return {
            "forecasts": _cache["data"],
            "cached": True,
            "generated_at": _cache["ts"],
        }

    logger.info("Forecast: generating new forecast from incident history")
    summary = await get_incidents_summary_for_memory(db, limit=30)
    forecasts = generate_forecast(summary)

    _cache = {"data": forecasts, "ts": now}

    return {
        "forecasts": forecasts,
        "cached": False,
        "generated_at": now,
    }