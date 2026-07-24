"""FastAPI REST API for Discord issue management."""

from fastapi import FastAPI

from .routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Discord MCP Issue API",
        description="REST API for querying Discord issue captures and sending replies",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    app.include_router(router, prefix="/api")
    return app
