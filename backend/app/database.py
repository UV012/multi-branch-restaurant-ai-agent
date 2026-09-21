"""Database Connection and Session Management."""

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from backend.app.config import settings

# Async Engine for application CRUD operations
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async DB session in FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and required extensions."""
    async with engine.begin() as conn:
        # Enable btree_gist extension for PostgreSQL exclusion constraint on reservations
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist;"))
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
