from __future__ import annotations
import contextlib
import ssl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from shared.config import settings
from shared.logger import get_logger

logger = get_logger("Database")


def _get_connect_args():
    if settings.POSTGRES_SSL_CA:
        ctx = ssl.create_default_context(cafile=settings.POSTGRES_SSL_CA)
        return {"ssl": ctx}
    return {}


engine = create_async_engine(
    settings.postgres_url,
    future=True,
    connect_args=_get_connect_args()
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
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