from pathlib import Path

import pytest

from kakuro import create_app
from kakuro.extensions import db


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    session_dir = tmp_path / "sessions"
    Path(session_dir).mkdir(parents=True, exist_ok=True)

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SESSION_TYPE": "filesystem",
            "SESSION_FILE_DIR": str(session_dir),
            "SECRET_KEY": "test-secret",
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
