"""FastAPI dependency injection providers."""

import logging
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from ..config import load_database_config
from .discord_gateway import DiscordGateway
from .repository import IssueRepository, UserRepository
from .service import AuthService, IssueQueryService

logger = logging.getLogger("discord-mcp-api.deps")

_engine = None
_gateway = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _get_engine():
    """Get or create the SQLModel async engine (singleton)."""
    global _engine
    if _engine is None:
        config = load_database_config()
        if not config.database_url:
            raise RuntimeError("DATABASE_URL not configured")
        url = config.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        _engine = create_async_engine(url, echo=False)
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    engine = _get_engine()
    async with AsyncSession(engine) as session:
        yield session


async def get_issue_repository(
    session: AsyncSession = Depends(get_session),
) -> IssueRepository:
    """Provide an IssueRepository dependency."""
    return IssueRepository(session)


def get_discord_gateway() -> DiscordGateway:
    """Provide a DiscordGateway singleton."""
    global _gateway
    if _gateway is None:
        _gateway = DiscordGateway()
    return _gateway


async def get_issue_service(
    repository: IssueRepository = Depends(get_issue_repository),
    gateway: DiscordGateway = Depends(get_discord_gateway),
) -> IssueQueryService:
    """Provide an IssueQueryService dependency."""
    return IssueQueryService(repository, gateway)


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    """Provide a UserRepository dependency."""
    return UserRepository(session)


async def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Provide an AuthService dependency."""
    return AuthService(repository)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Extract and validate the current user from the JWT token.

    Raises HTTPException 401 if the token is invalid or the user is not found.
    """
    user = await auth_service.get_current_user_from_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
