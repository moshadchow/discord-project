import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    database_url: str | None

    @property
    def capture_enabled(self) -> bool:
        return bool(self.database_url)


def load_database_config() -> DatabaseConfig:
    return DatabaseConfig(database_url=os.getenv("DATABASE_URL"))


@dataclass(frozen=True)
class MonitoredChannelsConfig:
    channel_ids: frozenset[str]
    channel_names: frozenset[str]

    @property
    def enabled(self) -> bool:
        return bool(self.channel_ids or self.channel_names)

    def matches_channel(self, channel: object) -> bool:
        channel_id = getattr(channel, "id", None)
        if channel_id is not None and str(channel_id) in self.channel_ids:
            return True

        channel_name = getattr(channel, "name", None)
        if channel_name is not None and str(channel_name) in self.channel_names:
            return True

        return False


def load_monitored_channels_config() -> MonitoredChannelsConfig:
    return MonitoredChannelsConfig(
        channel_ids=_parse_csv_env("DISCORD_MONITORED_CHANNEL_IDS"),
        channel_names=_parse_csv_env("DISCORD_MONITORED_CHANNELS"),
    )


def _parse_csv_env(name: str) -> frozenset[str]:
    value = os.getenv(name, "")
    return frozenset(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class AuthConfig:
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int


def load_auth_config() -> AuthConfig:
    return AuthConfig(
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_expire_minutes=int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
        ),
    )
