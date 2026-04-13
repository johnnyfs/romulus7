from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=settings.ECHO_SQL)
make_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with make_session() as session:
        yield session


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return make_session


async def dispose_engine() -> None:
    await engine.dispose()
