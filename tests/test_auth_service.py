import pytest

from kakuro.services.auth_service import hash_password, register_user, verify_password


def test_password_hashing_and_verification():
    password = "myStrongPassword"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(hashed, password)
    assert not verify_password(hashed, "wrong-password")


def test_username_and_email_uniqueness(app):
    with app.app_context():
        register_user("alice", "alice@example.com", "secret123")

        with pytest.raises(ValueError, match="Username already exists"):
            register_user("alice", "another@example.com", "secret123")

        with pytest.raises(ValueError, match="Email already exists"):
            register_user("alice2", "alice@example.com", "secret123")
