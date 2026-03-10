"""PostgreSQL database connection and session management."""

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

Base = declarative_base()

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


async def get_postgres_engine() -> AsyncEngine:
    """Get or create PostgreSQL engine."""
    global _engine
    
    if _engine is None:
        logger.info("Creating PostgreSQL engine", url=settings.postgres_url.split("@")[1])
        _engine = create_async_engine(
            settings.postgres_url,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    
    return _engine


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create session factory."""
    global _session_factory
    
    if _session_factory is None:
        engine = await get_postgres_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    factory = await get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_postgres_engine() -> None:
    """Close PostgreSQL engine."""
    global _engine, _session_factory
    
    if _engine is not None:
        logger.info("Closing PostgreSQL engine")
        await _engine.dispose()
        _engine = None
        _session_factory = None
