from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.database.database import Base


class MonitoredProject(Base):
    __tablename__ = "monitored_projects"

    id              = Column(Integer, primary_key=True, index=True)
    gitlab_project_id = Column(String, nullable=False, unique=True, index=True)
    name            = Column(String, nullable=False)
    description     = Column(String, nullable=True)
    active          = Column(Boolean, default=True, nullable=False)
    webhook_secret  = Column(String, nullable=True)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)