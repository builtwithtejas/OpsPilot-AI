# backend/app/models/incident.py

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.sql import expression
from app.database.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, nullable=False)
    severity    = Column(String, nullable=False)
    status      = Column(String, nullable=False, server_default="Open")
    description = Column(String, nullable=False)
    remediation = Column(String, nullable=False)
    confidence  = Column(Integer, nullable=False)

    source           = Column(String, nullable=True)
    pipeline_id      = Column(String, nullable=True)
    gitlab_issue_url = Column(String, nullable=True)
    autofix_mr_url   = Column(String, nullable=True)

    # FIX: Use server_default so Postgres supplies the value even if the ORM
    # omits the column from the INSERT. Keep the Python default too so the
    # returned object is populated without a round-trip.
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )