# backend/app/database/database.py
# FIX: Switched from sync SQLAlchemy to async (asyncpg + SQLAlchemy async).
#      Previously, every DB call blocked FastAPI's async event loop.
#      Now DB calls are fully non-blocking — safe under real concurrent load.
#
# REQUIRED: Add these to requirements.txt (see r1b_requirements.txt):
#   sqlalchemy[asyncio]==2.0.35
#   asyncpg==0.29.0
#
# REQUIRED: Change your DATABASE_URL in .env from:
#   DATABASE_URL=postgresql://user:pass@host/db
# to:
#   DATABASE_URL=postgresql+asyncpg://user:pass@host/db
#
# For local SQLite dev, use:
#   DATABASE_URL=sqlite+aiosqlite:///./opspilot.db
# and add aiosqlite to requirements.txt too.

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Detect SQLite (dev) vs Postgres (prod) — both need async drivers
_url = settings.DATABASE_URL

# Auto-upgrade bare sqlite:/// or postgresql:// URLs to async variants
# so existing .env files keep working without manual edits
if _url.startswith("sqlite:///") and "+aiosqlite" not in _url:
    _url = _url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
elif _url.startswith("postgresql://") and "+asyncpg" not in _url:
    _url = _url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _url.startswith("postgres://") and "+asyncpg" not in _url:
    _url = _url.replace("postgres://", "postgresql+asyncpg://", 1)

_is_sqlite = "sqlite" in _url

engine = create_async_engine(
    _url,
    echo=False,
    pool_pre_ping=True,
    # SQLite doesn't support connection pools — use StaticPool for dev
    **( {"connect_args": {"check_same_thread": False}} if _is_sqlite else {} ),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)