"""Unit tests for password hashing utilities."""

import unittest

from discord_mcp.core.security import hash_password, verify_password


class PasswordHashingTests(unittest.TestCase):
    """Tests for bcrypt password hashing."""

    def test_hash_password_returns_string(self):
        result = hash_password("Password@123")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_hash_password_is_not_plaintext(self):
        result = hash_password("Password@123")
        self.assertNotEqual(result, "Password@123")

    def test_verify_password_correct(self):
        hashed = hash_password("Password@123")
        self.assertTrue(verify_password("Password@123", hashed))

    def test_verify_password_incorrect(self):
        hashed = hash_password("Password@123")
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_different_hashes_for_same_password(self):
        hash1 = hash_password("Password@123")
        hash2 = hash_password("Password@123")
        self.assertNotEqual(hash1, hash2)

    def test_verify_empty_password(self):
        hashed = hash_password("")
        self.assertTrue(verify_password("", hashed))


if __name__ == "__main__":
    unittest.main()
