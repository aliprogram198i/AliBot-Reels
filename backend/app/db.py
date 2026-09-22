from __future__ import annotations
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): pass
def create_session_factory(database_url: str):
    kwargs = {"pool_pre_ping": True} if database_url.startswith("postgresql") else {}
    engine = create_async_engine(database_url, **kwargs)
    return engine, async_sessionmaker(engine, expire_on_commit=False)
async def get_db(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session: yield session
