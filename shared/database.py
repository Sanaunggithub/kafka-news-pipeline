from __future__ import annotations
import base64
import contextlib
import os
import ssl
import tempfile
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from shared.config import settings
from shared.logger import get_logger

logger = get_logger("Database")


def _get_connect_args():
    # Option 1 — cert content from env var (Render)
    if settings.POSTGRES_SSL_CA_CONTENT:
        ca_data = base64.b64decode(settings.POSTGRES_SSL_CA_CONTENT)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
        tmp.write(ca_data)
        tmp.flush()
        tmp.close()
        ctx = ssl.create_default_context(cafile=tmp.name)
        return {"ssl": ctx}

    # Option 2 — cert file path (local Docker)
    if settings.POSTGRES_SSL_CA and os.path.exists(settings.POSTGRES_SSL_CA):
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