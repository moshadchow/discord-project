"""Unit tests for authentication API route handlers."""

import unittest
from datetime import datetime
from unittest.mock import patch

from discord_mcp.core.security import hash_password


class FakeUserRow:
    """Minimal UserRow stand-in for route tests."""

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
    """In-memory user repository for route tests."""

    def __init__(self, users=None):
        self._users = list(users or [])
        self._next_id = max((u.id for u in self._users), default=0) + 1

    async def get_by_username(self, username):
        for u in self._users:
            if u.username == username:
                return u
        return None

    async def get_by_email(self, email):
        for u in self._users:
            if u.email == email:
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
        for u in self._users:
            if u.id == user_id:
                u.last_login_at = datetime.now()
                u.updated_at = datetime.now()


def _create_auth_test_app(users=None):
    """Create a FastAPI test app with mocked auth dependencies."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from discord_mcp.api.deps import get_auth_service, get_current_user, get_user_repository
    from discord_mcp.api.routes import auth_router
    from discord_mcp.api.service import AuthService

    app = FastAPI()
    app.include_router(auth_router, prefix="/api")

    repo = FakeUserRepository(users)
    auth_service = AuthService(repo)

    async def override_user_repository():
        return repo

    async def override_auth_service():
        return auth_service

    app.dependency_overrides[get_user_repository] = override_user_repository
    app.dependency_overrides[get_auth_service] = override_auth_service

    return app, TestClient(app), auth_service


class LoginTests(unittest.TestCase):
    """Tests for POST /api/auth/login."""

    @patch("discord_mcp.core.jwt.load_auth_config")
    def test_login_success(self, mock_config):
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
        app, client, _ = _create_auth_test_app([user])

        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Password@123"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["expires_in"], 86400)
        self.assertEqual(data["user"]["username"], "admin")
        self.assertEqual(data["user"]["role"], "Admin")

    def test_login_invalid_credentials(self):
        user = FakeUserRow()
        app, client, _ = _create_auth_test_app([user])

        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "WrongPassword"},
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("detail", data)

    def test_login_user_not_found(self):
        app, client, _ = _create_auth_test_app([])

        response = client.post(
            "/api/auth/login",
            json={"username": "nobody", "password": "Password@123"},
        )

        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        app, client, _ = _create_auth_test_app([])

        response = client.post("/api/auth/login", json={})

        self.assertEqual(response.status_code, 422)


class LogoutTests(unittest.TestCase):
    """Tests for POST /api/auth/logout."""

    def test_logout_success(self):
        app, client, _ = _create_auth_test_app([])

        response = client.post("/api/auth/logout")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Logged out successfully.")


class ProfileTests(unittest.TestCase):
    """Tests for GET /api/auth/profile."""

    @patch("discord_mcp.core.jwt.load_auth_config")
    def test_profile_returns_user(self, mock_config):
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
        app, client, auth_service = _create_auth_test_app([user])

        from discord_mcp.api.deps import get_current_user

        async def override_current_user():
            return await auth_service.get_current_user_from_token(token)

        from discord_mcp.core.jwt import create_access_token

        token = create_access_token(1, "admin", "Admin")
        app.dependency_overrides[get_current_user] = override_current_user

        response = client.get("/api/auth/profile")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "admin")
        self.assertEqual(data["full_name"], "Administrator")
        self.assertEqual(data["role"], "Admin")

    def test_profile_unauthorized_without_token(self):
        app, client, _ = _create_auth_test_app([])

        response = client.get("/api/auth/profile")

        self.assertEqual(response.status_code, 401)


class RegisterTests(unittest.TestCase):
    """Tests for POST /api/auth/register."""

    def test_register_success(self):
        app, client, _ = _create_auth_test_app([])

        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "Password@123",
                "confirm_password": "Password@123",
                "full_name": "New User",
                "email": "new@example.com",
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "User registered successfully.")
        self.assertEqual(data["data"]["username"], "newuser")
        self.assertEqual(data["data"]["full_name"], "New User")
        self.assertEqual(data["data"]["role"], "User")
        self.assertNotIn("password", data["data"])
        self.assertNotIn("password_hash", data["data"])

    def test_register_duplicate_username(self):
        user = FakeUserRow(username="existing")
        app, client, _ = _create_auth_test_app([user])

        response = client.post(
            "/api/auth/register",
            json={
                "username": "existing",
                "password": "Password@123",
                "confirm_password": "Password@123",
                "full_name": "Duplicate",
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_register_duplicate_email(self):
        user = FakeUserRow(email="taken@example.com")
        app, client, _ = _create_auth_test_app([user])

        response = client.post(
            "/api/auth/register",
            json={
                "username": "another",
                "password": "Password@123",
                "confirm_password": "Password@123",
                "full_name": "Another User",
                "email": "taken@example.com",
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_register_password_mismatch(self):
        app, client, _ = _create_auth_test_app([])

        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "Password@123",
                "confirm_password": "DifferentPassword",
                "full_name": "New User",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        app, client, _ = _create_auth_test_app([])

        response = client.post("/api/auth/register", json={})

        self.assertEqual(response.status_code, 422)

    def test_register_optional_email(self):
        app, client, _ = _create_auth_test_app([])

        response = client.post(
            "/api/auth/register",
            json={
                "username": "noemail",
                "password": "Password@123",
                "confirm_password": "Password@123",
                "full_name": "No Email",
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["data"]["username"], "noemail")


if __name__ == "__main__":
    unittest.main()
