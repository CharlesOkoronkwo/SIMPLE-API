import sqlite3
from datetime import datetime
from pathlib import Path

from . import config

SCHEMA_FILE = Path(__file__).with_name("schema.sql")
SCHEMA_VERSION = 3


def connect(path=None):
    """Open the database, creating the file and tables if they are missing."""
    path = str(path or config.db_path())
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn):
    conn.executescript(SCHEMA_FILE.read_text())
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current < SCHEMA_VERSION:
        conn.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)
    conn.commit()


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def one(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()


def many(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()


def scalar(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return None
    return row[0]
