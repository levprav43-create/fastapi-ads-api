# app/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Подключение к PostgreSQL в Docker (порт 5433)
DATABASE_URL = "postgresql+psycopg://ads_user:ads_password@localhost:5433/ads_db"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """ЕДИНАЯ база для всех моделей проекта."""
    pass


async def init_db():
    """Создаёт все таблицы при старте сервера."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия БД для роутов (используется в Depends)."""
    async with async_session_maker() as session:
        yield session