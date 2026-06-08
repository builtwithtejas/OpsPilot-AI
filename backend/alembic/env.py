# C-4 FIX (alembic): asyncpg rejects ?sslmode=require in the URL.
# Use connect_args={"ssl": "require"} instead for Neon/production Postgres.

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

from app.database.database import Base
from app.models import incident, deployment, audit_log          # noqa: F401
from app.models.monitored_project import MonitoredProject       # noqa: F401
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _async_url(url: str) -> str:
    """Upgrade bare driver prefixes to async variants. Strip sslmode query param."""
    import re
    # Remove ?sslmode=... or &sslmode=... — asyncpg rejects it in the URL
    url = re.sub(r"[?&]sslmode=[^&]*", "", url)
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://") and "+asyncpg" not in url:
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


_db_url = _async_url(settings.DATABASE_URL)
_is_postgres = "postgresql+asyncpg" in _db_url

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # C-4 FIX: pass ssl="require" via connect_args for Postgres; not in the URL
    connect_args: dict = {"ssl": "require"} if _is_postgres else {}

    connectable = create_async_engine(
        _db_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
