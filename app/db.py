import sqlite3

import click
from flask import current_app, g


def get_db():
    """Open one database connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            timeout=10,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(error=None):
    """Close the connection when Flask finishes using it."""
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Create the tables defined in schema.sql."""
    db = get_db()

    with current_app.open_resource("schema.sql") as schema:
        db.executescript(schema.read().decode("utf-8"))

    db.commit()


@click.command("init-db")
def init_db_command():
    """Create the application's database tables."""
    init_db()
    click.echo("Database tables initialized.")


def init_app(app):
    """Register database cleanup and the setup command."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)