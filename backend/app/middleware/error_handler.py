from fastapi import Request
from fastapi.responses import JSONResponse
from tenacity import RetryError
from app.utils.logger import logger


async def retry_exception_handler(request: Request, exc: RetryError):
    logger.error("Retry exhausted on %s: %s", request.url, exc)
    return JSONResponse(status_code=503, content={"detail": "External service failed after retries. Please try again later."})


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})
