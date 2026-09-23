import os

from flask import Flask


def create_app(test_config=None):
    """Create and configure the student portal."""
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, "portal.sqlite"),
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    from app import db
    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app