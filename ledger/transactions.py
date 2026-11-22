import sqlite3

from . import accounts, categories, db
from .dates import ISO_RE, day_before
from .models import Transaction
from .money import round_kobo


def check_date(text):
    if not ISO_RE.fullmatch(text or ""):
        raise ValueError("date must look like 2025-03-31")
    return text


def add_transaction(conn, account_id, posted_on, description, amount,
                    reference=None, category=None, source_file=None):
    """Add one transaction by hand. Amount is negative for money going out."""
    accounts.get_account(conn, account_id)
    check_date(posted_on)
    description = (description or "").strip()
    if not description:
        raise ValueError("description is required")
    if category is None:
        category = categories.categorize(conn, description)
    try:
        cur = conn.execute(
            "INSERT INTO transactions "
            "(account_id, posted_on, description, amount, reference, category, source_file, imported_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (account_id, posted_on, description, float(amount), reference, category,
             source_file, db.now_text()),
        )
    except sqlite3.IntegrityError:
        raise ValueError("reference %r is already used on this account" % reference)
    conn.commit()
    return get_transaction(conn, cur.lastrowid)


def get_transaction(conn, tx_id):
    row = db.one(conn, "SELECT * FROM transactions WHERE id = ?", (tx_id,))
    if row is None:
        raise LookupError("no transaction with id %s" % tx_id)
    return Transaction.from_row(row)


def list_transactions(conn, account_id, start=None, end=None, category=None,
                      text=None, limit=200, offset=0):
    accounts.get_account(conn, account_id)
    sql = "SELECT * FROM transactions WHERE account_id = ?"
    params = [account_id]
    if start:
        sql += " AND posted_on >= ?"
        params.append(check_date(start))
    if end:
        sql += " AND posted_on <= ?"
        params.append(check_date(end))
    if category:
        sql += " AND category = ?"
        params.append(category)
    if text:
        sql += " AND description LIKE ?"
        params.append("%" + text + "%")
    sql += " ORDER BY posted_on, id LIMIT ? OFFSET ?"
    params.extend([int(limit), int(offset)])
    return [Transaction.from_row(r) for r in db.many(conn, sql, params)]


def count_transactions(conn, account_id, start=None, end=None):
    sql = "SELECT COUNT(*) FROM transactions WHERE account_id = ?"
    params = [account_id]
    if start:
        sql += " AND posted_on >= ?"
        params.append(start)
    if end:
        sql += " AND posted_on <= ?"
        params.append(end)
    return db.scalar(conn, sql, params)


def update_transaction(conn, tx_id, description=None, category=None):
    tx = get_transaction(conn, tx_id)
    if description is not None:
        description = description.strip()
        if not description:
            raise ValueError("description cannot be empty")
        conn.execute("UPDATE transactions SET description = ? WHERE id = ?", (description, tx_id))
    if category is not None:
        conn.execute("UPDATE transactions SET category = ? WHERE id = ?", (category, tx_id))
    conn.commit()
    return get_transaction(conn, tx.id)


def delete_transaction(conn, tx_id):
    get_transaction(conn, tx_id)
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()


def balance_as_of(conn, account_id, as_of):
    """Opening balance plus everything posted up to and including as_of."""
    account = accounts.get_account(conn, account_id)
    check_date(as_of)
    moved = db.scalar(
        conn,
        "SELECT COALESCE(SUM(amount), 0) FROM transactions "
        "WHERE account_id = ? AND posted_on <= ?",
        (account_id, as_of),
    )
    return round_kobo(account.opening_balance + moved)


def balance_before(conn, account_id, day):
    """Balance at the end of the day before `day`."""
    return balance_as_of(conn, account_id, day_before(day))


def running_balance(conn, account_id, start, end):
    """List of (date, balance at end of that day) for days that had activity."""
    opening = balance_before(conn, account_id, start)
    rows = db.many(
        conn,
        "SELECT posted_on, SUM(amount) AS moved FROM transactions "
        "WHERE account_id = ? AND posted_on BETWEEN ? AND ? "
        "GROUP BY posted_on ORDER BY posted_on",
        (account_id, start, end),
    )
    series = []
    balance = opening
    for row in rows:
        balance += row["moved"]
        series.append({"date": row["posted_on"], "balance": round_kobo(balance)})
    return series


def search(conn, account_id, text, limit=50):
    return list_transactions(conn, account_id, text=text, limit=limit)
