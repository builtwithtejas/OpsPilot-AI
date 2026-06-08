# C-4 FIX: asyncpg rejects ?sslmode=require in the URL.
#   The sslmode parameter must NOT be in the URL for asyncpg.
#   Instead, SSL is configured via connect_args={"ssl": "require"} (asyncpg accepts a string).
#   The DATABASE_URL in .env should be plain postgresql+asyncpg://... (no sslmode query param).
#
# database.py — async SQLAlchemy engine for FastAPI

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.core.config import settings

_url = settings.DATABASE_URL

# Auto-upgrade bare sqlite:/// or postgresql:// URLs to async variants
if _url.startswith("sqlite:///") and "+aiosqlite" not in _url:
    _url = _url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
elif _url.startswith("postgresql://") and "+asyncpg" not in _url:
    _url = _url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _url.startswith("postgres://") and "+asyncpg" not in _url:
    _url = _url.replace("postgres://", "postgresql+asyncpg://", 1)

_is_sqlite = "sqlite" in _url
_is_postgres = "postgresql+asyncpg" in _url

# C-4 FIX: For Neon / any production Postgres, pass ssl="require" via connect_args.
# asyncpg accepts "require", "disable", "prefer", or an ssl.SSLContext object.
# Do NOT put sslmode=require in the URL — asyncpg will reject it.
_connect_args: dict = {}
if _is_sqlite:
    _connect_args = {"check_same_thread": False}
elif _is_postgres:
    _connect_args = {"ssl": "require"}

engine = create_async_engine(
    _url,
    echo=False,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
