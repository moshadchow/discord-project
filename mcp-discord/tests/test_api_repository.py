"""Unit tests for the issue repository."""

import unittest
from datetime import date, datetime, time
from unittest.mock import AsyncMock, MagicMock


class FakeRow:
    """Minimal IssueRow stand-in for repository tests."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class IssueRepositoryTests(unittest.IsolatedAsyncioTestCase):
    """Tests for IssueRepository query and write methods."""

    def _make_repo(self, mock_session):
        from discord_mcp.api.repository import IssueRepository

        return IssueRepository(mock_session)

    async def test_get_by_message_id_returns_none_when_not_found(self):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        repo = self._make_repo(mock_session)
        result = await repo.get_by_discord_message_id("nonexistent")
        self.assertIsNone(result)

    async def test_get_by_message_id_returns_row_when_found(self):
        expected = FakeRow(discord_message_id="123", sender="alice")
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = expected
        mock_session.exec.return_value = mock_result

        repo = self._make_repo(mock_session)
        result = await repo.get_by_discord_message_id("123")
        self.assertEqual(result.discord_message_id, "123")
        self.assertEqual(result.sender, "alice")

    async def test_get_by_channel_id_returns_list(self):
        rows = [FakeRow(channel_id="ch1"), FakeRow(channel_id="ch1")]
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = rows
        mock_session.exec.return_value = mock_result

        repo = self._make_repo(mock_session)
        result = await repo.get_by_channel_id("ch1")
        self.assertEqual(len(result), 2)

    async def test_get_by_sender_returns_rows_and_total(self):
        rows = [FakeRow(sender="bob")]
        mock_session = AsyncMock()

        count_result = MagicMock()
        count_result.one.return_value = 5

        query_result = MagicMock()
        query_result.all.return_value = rows

        mock_session.exec.side_effect = [count_result, query_result]

        repo = self._make_repo(mock_session)
        result_rows, total = await repo.get_by_sender("bob", skip=0, limit=10)
        self.assertEqual(len(result_rows), 1)
        self.assertEqual(total, 5)

    async def test_create_issue_adds_and_refreshes(self):
        mock_session = AsyncMock()
        row = FakeRow(discord_message_id="456")

        repo = self._make_repo(mock_session)
        result = await repo.create_issue(row)

        mock_session.add.assert_called_once_with(row)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(row)
        self.assertEqual(result.discord_message_id, "456")

    async def test_delete_by_message_id_returns_true_when_deleted(self):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec.return_value = mock_result

        repo = self._make_repo(mock_session)
        result = await repo.delete_by_discord_message_id("123")
        self.assertTrue(result)
        mock_session.commit.assert_called_once()

    async def test_delete_by_message_id_returns_false_when_no_match(self):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec.return_value = mock_result

        repo = self._make_repo(mock_session)
        result = await repo.delete_by_discord_message_id("nonexistent")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
