# backend/app/database/dependencies.py
# FIX: get_db is now an async generator yielding AsyncSession.
#      All route functions that use Depends(get_db) must become async def.
#      See the route fixes in r1c_routes_async_note.txt for the pattern.

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
