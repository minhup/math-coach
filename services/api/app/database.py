from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()
if settings.environment == "test":
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
    )
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_database_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
