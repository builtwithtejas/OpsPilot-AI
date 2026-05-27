from fastapi import APIRouter, Depends
from app.core.security import require_api_key
from app.services.metrics_service import get_system_metrics

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/", summary="Real-time system metrics", dependencies=[Depends(require_api_key)])
def metrics():
    return get_system_metrics()
