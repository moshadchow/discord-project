import asyncio
import contextlib
import io
import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seed import SeedOptions, parse_args, resolve_channel, retrieve_messages


class SeedArgumentTests(unittest.TestCase):
    def test_parse_args_accepts_dates_and_limit(self):
        options = parse_args(
            [
                "--channel",
                "support-issues",
                "--limit",
                "500",
                "--from-date",
                "2026-01-01",
                "--to-date",
                "2026-06-30",
            ]
        )

        self.assertEqual(options.channel, "support-issues")
        self.assertEqual(options.limit, 500)
        self.assertEqual(options.from_date, date(2026, 1, 1))
        self.assertEqual(options.to_date, date(2026, 6, 30))

    def test_parse_args_rejects_invalid_date_range(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(
                [
                    "--channel",
                    "support-issues",
                    "--from-date",
                    "2026-06-30",
                    "--to-date",
                    "2026-01-01",
                ]
            )


class SeedChannelResolutionTests(unittest.TestCase):
    def test_resolve_channel_returns_exact_single_match(self):
        channel = _channel("issues", 123, "Support")
        client = SimpleNamespace(guilds=[channel.guild])

        self.assertIs(resolve_channel(client, "issues"), channel)

    def test_resolve_channel_rejects_missing_channel(self):
        client = SimpleNamespace(guilds=[_guild("Support", [_channel("general")])])

        with self.assertRaisesRegex(RuntimeError, "No text channel"):
            resolve_channel(client, "issues")

    def test_resolve_channel_rejects_ambiguous_channel_names(self):
        first = _channel("issues", 123, "Support")
        second = _channel("issues", 456, "Ops")
        client = SimpleNamespace(guilds=[first.guild, second.guild])

        with self.assertRaisesRegex(RuntimeError, "Multiple text channels"):
            resolve_channel(client, "issues")


class SeedMessageRetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_retrieve_messages_returns_oldest_first(self):
        newest_first_messages = [
            SimpleNamespace(id=3),
            SimpleNamespace(id=2),
            SimpleNamespace(id=1),
        ]
        channel = FakeHistoryChannel(newest_first_messages)
        options = SeedOptions(
            channel="issues",
            limit=3,
            from_date=date(2026, 1, 1),
            to_date=date(2026, 1, 31),
        )

        messages = await retrieve_messages(channel, options)

        self.assertEqual([message.id for message in messages], [1, 2, 3])
        self.assertEqual(channel.history_kwargs["limit"], 3)
        self.assertIsNotNone(channel.history_kwargs["after"])
        self.assertIsNotNone(channel.history_kwargs["before"])


class FakeHistoryChannel:
    def __init__(self, messages):
        self._messages = messages
        self.history_kwargs = None

    def history(self, **kwargs):
        self.history_kwargs = kwargs
        return _async_iter(self._messages)


async def _async_iter(values):
    for value in values:
        await asyncio.sleep(0)
        yield value


def _channel(name, channel_id=1, guild_name="Support"):
    channel = SimpleNamespace(id=channel_id, name=name)
    guild = _guild(guild_name, [channel])
    channel.guild = guild
    return channel


def _guild(name, channels):
    guild = SimpleNamespace(name=name, id=len(name), text_channels=channels)
    for channel in channels:
        channel.guild = guild
    return guild
