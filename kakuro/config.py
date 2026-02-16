from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "kakuro.sqlite"
SCHEMA_PATH = DB_DIR / "schema.sql"


class Config:
    SECRET_KEY = "dev-secret-key-change-in-production"
    SESSION_PERMANENT = False
    TEMPLATES_AUTO_RELOAD = True
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = str(BASE_DIR / ".flask_session")
    SESSION_USE_SIGNER = True

    DB_PATH = DB_PATH
    SCHEMA_PATH = SCHEMA_PATH
