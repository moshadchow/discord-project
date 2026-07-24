import unittest
from datetime import datetime, time, timezone
from types import SimpleNamespace

from discord_mcp.issue_parser import IssueExtractionError, extract_issue


class IssueParserTests(unittest.TestCase):
    def test_uses_message_timestamp_when_date_and_time_are_absent(self):
        timestamp = datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc)
        author = SimpleNamespace(display_name="Ada", name="ada-user")

        issue = extract_issue("Production deploy failed", author, timestamp)

        self.assertEqual(issue.issue_date, timestamp.date())
        self.assertEqual(issue.issue_time.hour, 10)
        self.assertEqual(issue.issue_time.minute, 30)
        self.assertEqual(issue.sender, "Ada")
        self.assertEqual(issue.issue, "Production deploy failed")

    def test_extracts_iso_date_and_24_hour_time(self):
        timestamp = datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc)
        author = SimpleNamespace(display_name="Ada")

        issue = extract_issue("2026-08-15 outage at 14:45", author, timestamp)

        self.assertEqual(issue.issue_date.isoformat(), "2026-08-15")
        self.assertEqual(issue.issue_time.hour, 14)
        self.assertEqual(issue.issue_time.minute, 45)

    def test_extracts_supported_time_formats_without_hour_shift(self):
        timestamp = datetime(2026, 7, 12, 6, 30, tzinfo=timezone.utc)
        author = SimpleNamespace(display_name="Ada")
        samples = {
            "AM failure at 01:02:03.45": time(1, 2, 3, 450000),
            "PM failure at 11:02 PM": time(23, 2),
            "Noon failure at 12:33:45.22": time(12, 33, 45, 220000),
            "Midnight failure at 00:33:45.22": time(0, 33, 45, 220000),
            "Midnight 12-hour failure at 12:33:45.22 AM": time(0, 33, 45, 220000),
        }

        for content, expected_time in samples.items():
            with self.subTest(content=content):
                issue = extract_issue(content, author, timestamp)

                self.assertEqual(issue.issue_time, expected_time)

    def test_uses_author_name_when_display_name_is_missing(self):
        timestamp = datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc)
        author = SimpleNamespace(name="ada-user")

        issue = extract_issue("API latency is high", author, timestamp)

        self.assertEqual(issue.sender, "ada-user")

    def test_empty_message_raises_extraction_error(self):
        timestamp = datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc)

        with self.assertRaises(IssueExtractionError):
            extract_issue("   ", SimpleNamespace(name="Ada"), timestamp)
