import io

from ledger import accounts, export, transactions


def test_export_writes_header_and_rows(conn):
    acct = accounts.create_account(conn, "Main", "manual")
    transactions.add_transaction(conn, acct.id, "2025-03-01", "KFC", -3500.5)
    out = io.StringIO()
    count = export.export_csv(conn, acct.id, out)
    lines = out.getvalue().strip().splitlines()
    assert count == 1
    assert lines[0] == "date,description,amount,category,reference"
    assert lines[1] == "2025-03-01,KFC,-3500.50,eating out,"


def test_export_respects_dates(conn):
    acct = accounts.create_account(conn, "Main", "manual")
    transactions.add_transaction(conn, acct.id, "2025-03-01", "A", -1)
    transactions.add_transaction(conn, acct.id, "2025-04-01", "B", -1)
    out = io.StringIO()
    assert export.export_csv(conn, acct.id, out, start="2025-04-01") == 1
