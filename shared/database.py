from __future__ import annotations
import contextlib
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from shared.config import settings
from shared.logger import get_logger

logger = get_logger("Database")

engine = create_async_engine(
    settings.postgres_url,
    future=True,
    connect_args={"ssl": settings.POSTGRES_SSL_CA or False}
)


class Base(DeclarativeBase):
    pass


@contextlib.asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.warning("Database session failed, rolling back: %s", exc)
            raise