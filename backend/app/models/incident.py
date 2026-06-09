from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String, nullable=False)
    severity         = Column(String, nullable=False)
    status           = Column(String, nullable=False, default="Open")
    description      = Column(String, nullable=False)
    remediation      = Column(String, nullable=False)
    confidence       = Column(Integer, nullable=False)

    # GitLab fields
    source           = Column(String, nullable=True)           # "agent" | "upload" | "webhook"
    pipeline_id      = Column(String, nullable=True)           # GitLab pipeline ID
    gitlab_issue_url = Column(String, nullable=True)           # link to auto-created GitLab issue
    # add after gitlab_issue_url:
    autofix_mr_url   = Column(String, nullable=True)  # link to auto-fix MR

    created_at = Column(
    DateTime,
    default=datetime.utcnow,
    nullable=False,
)

updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow,
    nullable=False,
)