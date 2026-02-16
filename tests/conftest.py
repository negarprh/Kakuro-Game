from pathlib import Path

import pytest

from kakuro.app import create_app
from kakuro.models.user import init_db


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test_kakuro.sqlite"
    schema_path = Path("kakuro/db/schema.sql").resolve()

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DB_PATH": db_path,
            "SCHEMA_PATH": schema_path,
        }
    )

    init_db(db_path=db_path, schema_path=schema_path)

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
