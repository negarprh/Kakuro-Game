import os

import click
from flask import Flask, g, session

from config import Config, INSTANCE_DIR
from .extensions import db, session_ext
from .repositories.user_repository import UserRepository


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    os.makedirs(INSTANCE_DIR, exist_ok=True)
    if app.config.get("SESSION_TYPE") == "filesystem":
        session_dir = app.config.get("SESSION_FILE_DIR")
        if session_dir:
            os.makedirs(session_dir, exist_ok=True)

    db.init_app(app)
    session_ext.init_app(app)

    from .routes.auth import auth_bp
    from .routes.game import game_bp
    from .routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)

    @app.before_request
    def load_current_user():
        user_id = session.get("user_id")
        g.current_user = UserRepository.get_by_id(user_id) if user_id else None

    @app.context_processor
    def inject_layout_context():
        return {
            "user_mode": session.get("user_mode"),
            "current_user": g.get("current_user"),
        }

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        click.echo("Database initialized.")

    with app.app_context():
        db.create_all()

    return app
