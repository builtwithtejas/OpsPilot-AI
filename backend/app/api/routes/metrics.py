# C-1 FIX: psutil.cpu_percent(interval=0.5) blocks for 500ms.
# Run it in a thread pool via asyncio.to_thread so it doesn't freeze the event loop.

import asyncio
from fastapi import APIRouter, Depends
from app.core.security import require_api_key
from app.services.metrics_service import get_system_metrics

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/", summary="Real-time system metrics", dependencies=[Depends(require_api_key)])
async def metrics():
    return await asyncio.to_thread(get_system_metrics)
