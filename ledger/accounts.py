import sqlite3

from . import config, db
from .models import Account


def create_account(conn, name, layout, opening_balance=0.0):
    name = (name or "").strip()
    if not name:
        raise ValueError("account name is required")
    if layout not in config.LAYOUTS:
        raise ValueError("layout must be one of: %s" % ", ".join(config.LAYOUTS))
    try:
        cur = conn.execute(
            "INSERT INTO accounts (name, layout, opening_balance, currency, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, layout, float(opening_balance), config.CURRENCY, db.now_text()),
        )
    except sqlite3.IntegrityError:
        raise ValueError("an account called %r already exists" % name)
    conn.commit()
    return get_account(conn, cur.lastrowid)


def get_account(conn, account_id):
    row = db.one(conn, "SELECT * FROM accounts WHERE id = ?", (account_id,))
    if row is None:
        raise LookupError("no account with id %s" % account_id)
    return Account.from_row(row)


def list_accounts(conn):
    rows = db.many(conn, "SELECT * FROM accounts ORDER BY id")
    return [Account.from_row(r) for r in rows]


def find_by_name(conn, name):
    row = db.one(conn, "SELECT * FROM accounts WHERE name = ?", (name,))
    if row is None:
        return None
    return Account.from_row(row)


def rename_account(conn, account_id, new_name):
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("account name is required")
    get_account(conn, account_id)
    try:
        conn.execute("UPDATE accounts SET name = ? WHERE id = ?", (new_name, account_id))
    except sqlite3.IntegrityError:
        raise ValueError("an account called %r already exists" % new_name)
    conn.commit()
    return get_account(conn, account_id)


def set_opening_balance(conn, account_id, amount):
    get_account(conn, account_id)
    conn.execute(
        "UPDATE accounts SET opening_balance = ? WHERE id = ?", (float(amount), account_id)
    )
    conn.commit()
    return get_account(conn, account_id)


def delete_account(conn, account_id):
    """Only empty accounts can be deleted."""
    get_account(conn, account_id)
    used = db.scalar(
        conn, "SELECT COUNT(*) FROM transactions WHERE account_id = ?", (account_id,)
    )
    if used:
        raise ValueError("account still has %d transactions" % used)
    conn.execute("DELETE FROM budgets WHERE account_id = ?", (account_id,))
    conn.execute("DELETE FROM imports WHERE account_id = ?", (account_id,))
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
