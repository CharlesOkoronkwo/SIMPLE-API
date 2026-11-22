import csv

from . import transactions

COLUMNS = ["date", "description", "amount", "category", "reference"]


def export_csv(conn, account_id, handle, start=None, end=None):
    """Write an account's transactions to an open text file. Returns the row count."""
    rows = transactions.list_transactions(
        conn, account_id, start=start, end=end, limit=1000000
    )
    writer = csv.writer(handle)
    writer.writerow(COLUMNS)
    for tx in rows:
        writer.writerow(
            [tx.posted_on, tx.description, "%.2f" % tx.amount, tx.category or "", tx.reference or ""]
        )
    return len(rows)
