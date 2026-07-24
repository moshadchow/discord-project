"""FastAPI REST API for Discord issue management."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from .routes import auth_router, issue_router

logger = logging.getLogger("discord-mcp-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the users table on startup if it doesn't exist."""
    from .deps import _get_engine
    from .repository import UserRepository

    engine = _get_engine()
    try:
        async with AsyncSession(engine) as session:
            repo = UserRepository(session)
            await repo.ensure_users_table()
            logger.info("Users table verified")
    except Exception:
        logger.exception("Failed to ensure users table")
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Discord MCP Issue API",
        description="REST API for querying Discord issue captures and sending replies",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    app.include_router(auth_router, prefix="/api")
    app.include_router(issue_router, prefix="/api")
    return app
