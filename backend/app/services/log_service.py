from __future__ import annotations

import mimetypes
import os
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.utils.logger import logger

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


async def save_log_file(file: UploadFile) -> Path:
    _validate_upload(file)

    contents = await file.read()

    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # Sanitize filename — strip path components, keep only safe chars
    safe_name = Path(file.filename or "upload.log").name
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")[:100]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filepath = UPLOAD_DIR / f"{timestamp}_{safe_name}"

    filepath.write_bytes(contents)
    logger.info("Saved upload: %s (%d bytes)", filepath, len(contents))
    return filepath


def read_log_file(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.error("Failed to read log file %s: %s", filepath, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read uploaded file.",
        )


def _validate_upload(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".log", ".txt", ""}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{suffix}' not allowed. Upload .log or .txt files.",
        )

    content_type = file.content_type or ""
    guessed, _ = mimetypes.guess_type(file.filename)
    allowed = {"text/plain", "application/octet-stream", "text/x-log", None}
    if content_type not in allowed and guessed not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content type '{content_type}' not allowed.",
        )
