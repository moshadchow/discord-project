import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from discord_mcp.config import (
    MonitoredChannelsConfig,
    load_monitored_channels_config,
)


class MonitoredChannelsConfigTests(unittest.TestCase):
    def test_loads_comma_separated_channel_ids(self):
        with patch.dict(
            os.environ,
            {"DISCORD_MONITORED_CHANNEL_IDS": "123, 456,,789"},
            clear=True,
        ):
            config = load_monitored_channels_config()

        self.assertEqual(config.channel_ids, frozenset({"123", "456", "789"}))
        self.assertEqual(config.channel_names, frozenset())
        self.assertTrue(config.enabled)

    def test_loads_comma_separated_channel_names(self):
        with patch.dict(
            os.environ,
            {"DISCORD_MONITORED_CHANNELS": "support-issues, production-alerts"},
            clear=True,
        ):
            config = load_monitored_channels_config()

        self.assertEqual(
            config.channel_names,
            frozenset({"support-issues", "production-alerts"}),
        )
        self.assertEqual(config.channel_ids, frozenset())
        self.assertTrue(config.enabled)

    def test_disabled_when_no_channels_are_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            config = load_monitored_channels_config()

        self.assertFalse(config.enabled)

    def test_ids_and_names_are_additive(self):
        with patch.dict(
            os.environ,
            {
                "DISCORD_MONITORED_CHANNEL_IDS": "123",
                "DISCORD_MONITORED_CHANNELS": "support-issues",
            },
            clear=True,
        ):
            config = load_monitored_channels_config()

        self.assertTrue(config.matches_channel(SimpleNamespace(id=123, name="other")))
        self.assertTrue(
            config.matches_channel(SimpleNamespace(id=456, name="support-issues"))
        )

    def test_rejects_unconfigured_channel(self):
        config = MonitoredChannelsConfig(
            channel_ids=frozenset({"123"}),
            channel_names=frozenset({"support-issues"}),
        )

        self.assertFalse(
            config.matches_channel(SimpleNamespace(id=456, name="production-alerts"))
        )
