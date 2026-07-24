import argparse
import asyncio
import logging
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import discord
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from discord_mcp.config import load_database_config  # noqa: E402
from discord_mcp.issue_capture import IssueCaptureService, IssueCaptureStatus  # noqa: E402
from discord_mcp.issues_repository import IssuesRepository  # noqa: E402


logger = logging.getLogger("discord-mcp-seed")


@dataclass(frozen=True)
class SeedOptions:
    channel: str
    limit: int | None
    from_date: date | None
    to_date: date | None


def parse_args(argv: list[str] | None = None) -> SeedOptions:
    parser = argparse.ArgumentParser(
        description="Backfill historical Discord issue messages into PostgreSQL."
    )
    parser.add_argument("--channel", required=True, help="Discord channel name")
    parser.add_argument(
        "--limit",
        type=_positive_int,
        default=None,
        help="Maximum number of historical messages to retrieve",
    )
    parser.add_argument(
        "--from-date",
        type=_parse_date,
        default=None,
        help="Inclusive start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--to-date",
        type=_parse_date,
        default=None,
        help="Inclusive end date in YYYY-MM-DD format",
    )

    args = parser.parse_args(argv)
    if args.from_date and args.to_date and args.from_date > args.to_date:
        parser.error("--from-date must be on or before --to-date")

    return SeedOptions(
        channel=args.channel,
        limit=args.limit,
        from_date=args.from_date,
        to_date=args.to_date,
    )


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def run_seed(options: SeedOptions) -> Counter[str]:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN environment variable is required")

    database_config = load_database_config()
    if not database_config.capture_enabled:
        raise RuntimeError("DATABASE_URL environment variable is required")

    repository = IssuesRepository(database_config.database_url)
    await repository.open()

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    client = discord.Client(intents=intents)
    result: Counter[str] = Counter()
    failure: BaseException | None = None

    async def process_history() -> None:
        nonlocal result, failure
        started_at = datetime.now(timezone.utc)
        try:
            channel = resolve_channel(client, options.channel)
            logger.info(
                "Processing channel",
                extra={
                    "guild_id": str(channel.guild.id),
                    "guild_name": channel.guild.name,
                    "channel_id": str(channel.id),
                    "channel_name": channel.name,
                },
            )

            messages = await retrieve_messages(channel, options)
            logger.info("Retrieved %s historical messages", len(messages))

            service = IssueCaptureService(repository, logger)
            for message in messages:
                capture_result = await service.capture_message(message)
                result[capture_result.status.value] += 1

            result["retrieved"] = len(messages)
            duration = datetime.now(timezone.utc) - started_at
            logger.info(
                "Backfill complete: retrieved=%s inserted=%s duplicates=%s "
                "parse_failures=%s database_failures=%s duration_seconds=%.2f",
                result["retrieved"],
                result[IssueCaptureStatus.INSERTED.value],
                result[IssueCaptureStatus.DUPLICATE.value],
                result[IssueCaptureStatus.EXTRACTION_FAILED.value],
                result[IssueCaptureStatus.DATABASE_FAILED.value],
                duration.total_seconds(),
            )
        except BaseException as exc:
            failure = exc
        finally:
            await client.close()

    @client.event
    async def on_ready() -> None:
        logger.info("Logged in as %s", client.user)
        asyncio.create_task(process_history())

    try:
        await client.start(token)
    finally:
        await repository.close()

    if failure:
        raise failure

    return result


def resolve_channel(client: discord.Client, channel_name: str) -> discord.TextChannel:
    matches = [
        channel
        for guild in client.guilds
        for channel in guild.text_channels
        if channel.name == channel_name
    ]

    if not matches:
        raise RuntimeError(f"No text channel named {channel_name!r} was found")

    if len(matches) > 1:
        candidates = ", ".join(
            f"{channel.guild.name}/#{channel.name} ({channel.id})"
            for channel in matches
        )
        raise RuntimeError(
            f"Multiple text channels named {channel_name!r} were found: {candidates}"
        )

    return matches[0]


async def retrieve_messages(
    channel: discord.TextChannel, options: SeedOptions
) -> list[discord.Message]:
    after = _after_datetime(options.from_date)
    before = _before_datetime(options.to_date)
    messages = [
        message
        async for message in channel.history(
            limit=options.limit,
            after=after,
            before=before,
            oldest_first=False,
        )
    ]
    messages.reverse()
    return messages


def _after_datetime(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.min, tzinfo=timezone.utc) - timedelta(
        microseconds=1
    )


def _before_datetime(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value + timedelta(days=1), time.min, tzinfo=timezone.utc)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid YYYY-MM-DD date"
        ) from exc


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("--limit must be greater than zero")
    return parsed


async def async_main(argv: list[str] | None = None) -> int:
    configure_logging()
    load_dotenv(override=False)
    options = parse_args(argv)

    try:
        await run_seed(options)
    except Exception:
        logger.exception("Backfill failed")
        return 1

    return 0


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
