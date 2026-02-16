from kakuro.models.user import get_user_by_email
from kakuro.services.auth_service import submit_login, submit_signup


def test_signup_enforces_uniqueness(app):
    db_path = app.config["DB_PATH"]

    ok, _ = submit_signup(db_path, "alice", "alice@example.com", "secret123")
    assert ok is True

    ok, message = submit_signup(db_path, "alice", "other@example.com", "secret123")
    assert ok is False
    assert "Username already exists" in message

    ok, message = submit_signup(db_path, "bob", "alice@example.com", "secret123")
    assert ok is False
    assert "Email already exists" in message


def test_login_validation(app):
    db_path = app.config["DB_PATH"]

    ok, _ = submit_signup(db_path, "carol", "carol@example.com", "secret123")
    assert ok is True

    user = submit_login(db_path, "carol@example.com", "secret123")
    assert user is not None
    assert user.username == "carol"

    invalid = submit_login(db_path, "carol@example.com", "wrong")
    assert invalid is None


def test_signup_redirects_to_login(client):
    response = client.post(
        "/signup",
        data={
            "username": "dave",
            "email": "dave@example.com",
            "password": "secret123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
