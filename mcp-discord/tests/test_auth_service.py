"""Unit tests for the authentication service."""

import unittest
from datetime import datetime
from unittest.mock import patch

from discord_mcp.core.security import hash_password


class FakeUserRow:
    """Minimal UserRow stand-in for auth service tests."""

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "username": "admin",
            "password_hash": hash_password("Password@123"),
            "full_name": "Administrator",
            "email": "admin@example.com",
            "role": "Admin",
            "is_active": True,
            "last_login_at": None,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1),
        }
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


class FakeUserRepository:
    """In-memory user repository for auth service tests."""

    def __init__(self, users=None):
        self._users = list(users or [])
        self._next_id = max((u.id for u in self._users), default=0) + 1
        self._last_login_user_id = None

    async def get_by_username(self, username):
        for u in self._users:
            if u.username == username:
                return u
        return None

    async def get_by_id(self, user_id):
        for u in self._users:
            if u.id == user_id:
                return u
        return None

    async def create_user(self, row):
        row.id = self._next_id
        self._next_id += 1
        self._users.append(row)
        return row

    async def update_last_login(self, user_id):
        self._last_login_user_id = user_id
        for u in self._users:
            if u.id == user_id:
                u.last_login_at = datetime.now()
                u.updated_at = datetime.now()


class AuthenticateUserTests(unittest.IsolatedAsyncioTestCase):
    """Tests for AuthService.authenticate_user."""

    def _make_service(self, users=None):
        from discord_mcp.api.service import AuthService

        return AuthService(FakeUserRepository(users))

    @patch("discord_mcp.core.jwt.load_auth_config")
    async def test_authenticate_user_success(self, mock_config):
        mock_config.return_value = type(
            "Config",
            (),
            {
                "jwt_secret_key": "test-secret",
                "jwt_algorithm": "HS256",
                "jwt_access_token_expire_minutes": 1440,
            },
        )()
        user = FakeUserRow()
        service = self._make_service([user])

        user_dict, token = await service.authenticate_user("admin", "Password@123")

        self.assertIsNotNone(user_dict)
        self.assertIsNotNone(token)
        self.assertEqual(user_dict["username"], "admin")
        self.assertEqual(user_dict["role"], "Admin")

    async def test_authenticate_user_wrong_password(self):
        user = FakeUserRow()
        service = self._make_service([user])

        user_dict, error = await service.authenticate_user("admin", "WrongPassword")

        self.assertIsNone(user_dict)
        self.assertEqual(error, "Invalid username or password.")

    async def test_authenticate_user_not_found(self):
        service = self._make_service([])

        user_dict, error = await service.authenticate_user("nobody", "Password@123")

        self.assertIsNone(user_dict)
        self.assertEqual(error, "Invalid username or password.")

    async def test_authenticate_user_inactive(self):
        user = FakeUserRow(is_active=False)
        service = self._make_service([user])

        user_dict, error = await service.authenticate_user("admin", "Password@123")

        self.assertIsNone(user_dict)
        self.assertEqual(error, "Invalid username or password.")


class GetCurrentUserFromTokenTests(unittest.IsolatedAsyncioTestCase):
    """Tests for AuthService.get_current_user_from_token."""

    def _make_service(self, users=None):
        from discord_mcp.api.service import AuthService

        return AuthService(FakeUserRepository(users))

    @patch("discord_mcp.core.jwt.load_auth_config")
    async def test_valid_token_returns_user(self, mock_config):
        mock_config.return_value = type(
            "Config",
            (),
            {
                "jwt_secret_key": "test-secret",
                "jwt_algorithm": "HS256",
                "jwt_access_token_expire_minutes": 1440,
            },
        )()
        user = FakeUserRow(id=42)
        service = self._make_service([user])

        from discord_mcp.core.jwt import create_access_token

        token = create_access_token(42, "admin", "Admin")
        result = await service.get_current_user_from_token(token)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 42)
        self.assertEqual(result["username"], "admin")

    async def test_invalid_token_returns_none(self):
        service = self._make_service([])
        result = await service.get_current_user_from_token("invalid-token")
        self.assertIsNone(result)

    @patch("discord_mcp.core.jwt.load_auth_config")
    async def test_valid_token_but_user_not_found(self, mock_config):
        mock_config.return_value = type(
            "Config",
            (),
            {
                "jwt_secret_key": "test-secret",
                "jwt_algorithm": "HS256",
                "jwt_access_token_expire_minutes": 1440,
            },
        )()
        service = self._make_service([])

        from discord_mcp.core.jwt import create_access_token

        token = create_access_token(999, "ghost", "User")
        result = await service.get_current_user_from_token(token)

        self.assertIsNone(result)

    @patch("discord_mcp.core.jwt.load_auth_config")
    async def test_valid_token_but_inactive_user(self, mock_config):
        mock_config.return_value = type(
            "Config",
            (),
            {
                "jwt_secret_key": "test-secret",
                "jwt_algorithm": "HS256",
                "jwt_access_token_expire_minutes": 1440,
            },
        )()
        user = FakeUserRow(id=1, is_active=False)
        service = self._make_service([user])

        from discord_mcp.core.jwt import create_access_token

        token = create_access_token(1, "admin", "Admin")
        result = await service.get_current_user_from_token(token)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
