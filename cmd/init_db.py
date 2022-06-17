"""Creates the DB for the bot to save users' preferences.
If the bot session exists the DB is populated with the cached entities' data."""
import sqlite3
from pathlib import Path


DB = Path("files/bot-db.sqlite3")
SESSION_DB = Path("files/faffinity-bot.session")


if not DB.is_file():
    db_conn = sqlite3.connect(str(DB))

    with db_conn:
        db_conn.execute(
            """
            CREATE TABLE user (
                tid     INT64       PRIMARY KEY     NOT NULL,
                lang    VARCHAR(2)  DEFAULT 'es'    NOT NULL
            )
            """
        )
    print("Created table 'user'.")

    if SESSION_DB.is_file():
        session_conn = sqlite3.connect(str(SESSION_DB))

        with db_conn:
            for (id_,) in session_conn.execute("SELECT id FROM entities"):
                db_conn.execute(
                    "INSERT INTO user (tid) VALUES (?)",
                    (id_,)
                )

        session_conn.close()

        print("Populated DB with users cached in bot session.")

    db_conn.close()
