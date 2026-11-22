import pytest

from ledger import accounts, transactions
from ledger.importer import import_file, import_history

BANK_A = """
Date,Description,Debit,Credit,Balance
,Opening Balance,,,"100,000.00"
15/03/2025,POS PURCHASE SHOPRITE,"12,400.00",,"87,600.00"
16/03/2025,SALARY PAYMENT ACME,,"450,000.00","537,600.00"
20/03/2025,MTN AIRTIME,"1,000.00",,"536,600.00"
,Closing Balance,,,"536,600.00"
"""

BANK_B = """
Posted,Narration,Amount,Ref
2025-03-05,NIP TRANSFER TO ADA,(5000.00),FT1
2025-03-06,NIP TRANSFER FROM EMEKA,"8,000.00",FT2
2025-03-07,NIP TRANSFER TO KEMI,"(12,500.00)",FT3
,Closing balance,"90,500.00",
"""


@pytest.fixture
def current(conn):
    return accounts.create_account(conn, "Current", "bank_a", 100000)


@pytest.fixture
def savings(conn):
    return accounts.create_account(conn, "Savings", "bank_b", 100000)


def test_bank_a_import(conn, current, write_csv):
    result = import_file(conn, current.id, write_csv("a.csv", BANK_A))
    assert (result.rows_read, result.rows_added, result.rows_skipped) == (5, 3, 0)
    rows = transactions.list_transactions(conn, current.id)
    assert [t.amount for t in rows] == [-12400.0, 450000.0, -1000.0]
    assert [t.posted_on for t in rows] == ["2025-03-15", "2025-03-16", "2025-03-20"]


def test_bank_a_balance_matches_the_statement(conn, current, write_csv):
    import_file(conn, current.id, write_csv("a.csv", BANK_A))
    assert transactions.balance_as_of(conn, current.id, "2025-03-31") == 536600.0


def test_bank_a_categories_are_set(conn, current, write_csv):
    import_file(conn, current.id, write_csv("a.csv", BANK_A))
    cats = [t.category for t in transactions.list_transactions(conn, current.id)]
    assert cats == ["groceries", "income", "airtime"]


def test_bank_b_import_with_brackets(conn, savings, write_csv):
    result = import_file(conn, savings.id, write_csv("b.csv", BANK_B))
    assert result.rows_added == 3
    amounts = [t.amount for t in transactions.list_transactions(conn, savings.id)]
    assert amounts == [-5000.0, 8000.0, -12500.0]


def test_bank_b_references_are_kept(conn, savings, write_csv):
    import_file(conn, savings.id, write_csv("b.csv", BANK_B))
    refs = [t.reference for t in transactions.list_transactions(conn, savings.id)]
    assert refs == ["FT1", "FT2", "FT3"]


def test_bank_b_reimport_adds_nothing(conn, savings, write_csv):
    path = write_csv("b.csv", BANK_B)
    import_file(conn, savings.id, path)
    again = import_file(conn, savings.id, path)
    assert again.rows_added == 0
    assert transactions.count_transactions(conn, savings.id) == 3


def test_wrong_layout_for_the_account_is_refused(conn, savings, write_csv):
    with pytest.raises(ValueError):
        import_file(conn, savings.id, write_csv("a.csv", BANK_A))


def test_manual_account_detects_the_layout(conn, write_csv):
    manual = accounts.create_account(conn, "Loose", "manual")
    result = import_file(conn, manual.id, write_csv("b.csv", BANK_B))
    assert result.layout == "bank_b"


def test_unknown_file_is_refused(conn, write_csv):
    manual = accounts.create_account(conn, "Loose", "manual")
    with pytest.raises(ValueError):
        import_file(conn, manual.id, write_csv("x.csv", "one,two\n1,2\n"))


def test_unreadable_lines_are_skipped_and_reported(conn, savings, write_csv):
    text = BANK_B + "2025-03-09,BROKEN ROW,twelve,FT9\n"
    result = import_file(conn, savings.id, write_csv("b.csv", text))
    assert result.rows_added == 3
    assert result.rows_skipped == 1
    assert "twelve" in result.problems[0]


def test_bank_a_row_without_amount_is_skipped(conn, current, write_csv):
    text = BANK_A.replace('"12,400.00",,', ",,")
    result = import_file(conn, current.id, write_csv("a.csv", text))
    assert result.rows_skipped == 1


def test_bracketed_debit_is_still_a_debit(conn, current, write_csv):
    text = """
Date,Description,Debit,Credit,Balance
20/03/2025,POS PURCHASE (CARD HELD),(250.00),,"99,750.00"
"""
    import_file(conn, current.id, write_csv("a.csv", text))
    assert transactions.list_transactions(conn, current.id)[0].amount == -250.0


def test_import_history_is_recorded(conn, current, write_csv):
    import_file(conn, current.id, write_csv("a.csv", BANK_A))
    history = import_history(conn, current.id)
    assert history[0]["filename"] == "a.csv"
    assert history[0]["rows_added"] == 3


def test_byte_order_mark_is_ignored(conn, current, tmp_path):
    path = tmp_path / "bom.csv"
    path.write_bytes(b"\xef\xbb\xbf" + BANK_A.lstrip().encode("utf-8"))
    assert import_file(conn, current.id, path).rows_added == 3
