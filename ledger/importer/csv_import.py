import csv
from pathlib import Path

from .. import accounts, categories, db
from ..models import ImportResult
from .layouts import detect_layout, get_layout


def read_rows(path):
    """Read a statement file. Returns (header names, list of row dicts)."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return reader.fieldnames, rows


def import_file(conn, account_id, path, layout_name=None):
    """Load a bank statement into an account.

    The layout comes from the account unless one is given. Lines that cannot
    be read are skipped and listed in the result.
    """
    account = accounts.get_account(conn, account_id)
    path = Path(path)
    fieldnames, rows = read_rows(path)

    if layout_name or account.layout != "manual":
        layout = get_layout(layout_name or account.layout)
        if not layout.matches(fieldnames or []):
            raise ValueError(
                "%s does not have the columns of layout %s" % (path.name, layout.name)
            )
    else:
        layout = detect_layout(fieldnames)

    parsed, problems = layout.parse(rows)
    result = ImportResult(
        filename=path.name,
        layout=layout.name,
        rows_read=len(rows),
        rows_skipped=len(problems),
        problems=problems,
    )

    stamp = db.now_text()
    for row in parsed:
        category = categories.categorize(conn, row.description)
        cur = conn.execute(
            "INSERT OR IGNORE INTO transactions "
            "(account_id, posted_on, description, amount, reference, category, source_file, imported_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (account_id, row.posted_on, row.description, row.amount, row.reference,
             category, path.name, stamp),
        )
        result.rows_added += cur.rowcount

    conn.execute(
        "INSERT INTO imports (account_id, filename, layout, rows_read, rows_added, rows_skipped, imported_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (account_id, path.name, layout.name, result.rows_read, result.rows_added,
         result.rows_skipped, stamp),
    )
    conn.commit()
    return result


def import_history(conn, account_id):
    rows = db.many(
        conn,
        "SELECT filename, layout, rows_read, rows_added, rows_skipped, imported_at "
        "FROM imports WHERE account_id = ? ORDER BY id",
        (account_id,),
    )
    return [dict(r) for r in rows]
