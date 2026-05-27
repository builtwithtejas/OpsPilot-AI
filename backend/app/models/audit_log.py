from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id         = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, index=True, nullable=False)
    action     = Column(String, nullable=False)   # "created" | "status_changed" | "deleted"
    detail     = Column(String, nullable=True)    # human-readable detail
    actor      = Column(String, nullable=False, default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
