import pytest

from ledger import accounts, transactions


def test_create_and_get(conn):
    acct = accounts.create_account(conn, "Main", "bank_a", 1000)
    assert acct.id == 1
    assert accounts.get_account(conn, acct.id).opening_balance == 1000.0


def test_duplicate_name_is_refused(conn):
    accounts.create_account(conn, "Main", "manual")
    with pytest.raises(ValueError):
        accounts.create_account(conn, "Main", "manual")


def test_unknown_layout_is_refused(conn):
    with pytest.raises(ValueError):
        accounts.create_account(conn, "Main", "bank_z")


def test_blank_name_is_refused(conn):
    with pytest.raises(ValueError):
        accounts.create_account(conn, "  ", "manual")


def test_missing_account_raises_lookup_error(conn):
    with pytest.raises(LookupError):
        accounts.get_account(conn, 99)


def test_rename(conn):
    acct = accounts.create_account(conn, "Main", "manual")
    assert accounts.rename_account(conn, acct.id, "Salary").name == "Salary"


def test_rename_to_existing_name_is_refused(conn):
    accounts.create_account(conn, "A", "manual")
    b = accounts.create_account(conn, "B", "manual")
    with pytest.raises(ValueError):
        accounts.rename_account(conn, b.id, "A")


def test_cannot_delete_account_with_transactions(conn):
    acct = accounts.create_account(conn, "Main", "manual")
    transactions.add_transaction(conn, acct.id, "2025-03-01", "Coffee", -500)
    with pytest.raises(ValueError):
        accounts.delete_account(conn, acct.id)


def test_delete_empty_account(conn):
    acct = accounts.create_account(conn, "Main", "manual")
    accounts.delete_account(conn, acct.id)
    assert accounts.list_accounts(conn) == []


def test_find_by_name(conn):
    accounts.create_account(conn, "Main", "manual")
    assert accounts.find_by_name(conn, "Main").name == "Main"
    assert accounts.find_by_name(conn, "Other") is None
