from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.database.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Open")

    description = Column(String, nullable=False)
    remediation = Column(String, nullable=False)
    confidence = Column(Integer, nullable=False)

    # NEW
    source = Column(String, nullable=True)
    pipeline_id = Column(Integer, nullable=True)
    gitlab_issue_url = Column(String, nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
