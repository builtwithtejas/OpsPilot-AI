# M NOTE: This model exists for schema completeness and future use.
# Currently no service writes to the `deployments` table — workflow run data is
# fetched live from the GitHub API and returned directly.
# If you want to persist deployment history, add a service that writes here.
# Do NOT delete this model — Alembic tracks the table and dropping it requires a migration.
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database.database import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    workflow = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    commit = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    conclusion = Column(String, nullable=True)
    run_number = Column(Integer, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
