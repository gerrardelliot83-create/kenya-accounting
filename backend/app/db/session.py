"""
Database Session Configuration

Provides async database session management using SQLAlchemy 2.0.
Integrates with Supabase PostgreSQL via connection pooling.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool

from app.config import get_settings


# Global engine and session factory
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.

    Uses connection pooling for efficient database connections.
    Configuration is loaded from settings.

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    global _engine

    if _engine is None:
        settings = get_settings()

        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            # For serverless/pooled connections, consider using NullPool
            # poolclass=NullPool if settings.is_production else None
        )

    return _engine


def get_session_factory() -> async_sessionmaker:
    """
    Get or create the async session factory.

    Returns:
        async_sessionmaker: Factory for creating database sessions
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = get_engine()

        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False,
        )

    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields an async session and ensures proper cleanup.
    Use as a FastAPI dependency.

    Example:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session
            pass

    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting async database sessions.

    Use when you need a database session outside of FastAPI dependency injection.

    Example:
        async with get_db_context() as db:
            # Use db session
            pass

    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine():
    """
    Dispose of the database engine.

    Call this on application shutdown to clean up connections.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
