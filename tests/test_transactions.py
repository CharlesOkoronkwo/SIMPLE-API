import pytest

from ledger import accounts, transactions


@pytest.fixture
def acct(conn):
    return accounts.create_account(conn, "Main", "manual", 10000)


def add(conn, acct, day, desc, amount, **kw):
    return transactions.add_transaction(conn, acct.id, day, desc, amount, **kw)


def test_add_picks_a_category(conn, acct):
    tx = add(conn, acct, "2025-03-01", "KFC IKEJA", -3500)
    assert tx.category == "eating out"


def test_bad_date_is_refused(conn, acct):
    with pytest.raises(ValueError):
        add(conn, acct, "01/03/2025", "Coffee", -500)


def test_blank_description_is_refused(conn, acct):
    with pytest.raises(ValueError):
        add(conn, acct, "2025-03-01", " ", -500)


def test_reference_must_be_unique_per_account(conn, acct):
    add(conn, acct, "2025-03-01", "One", -1, reference="R1")
    with pytest.raises(ValueError):
        add(conn, acct, "2025-03-02", "Two", -1, reference="R1")


def test_list_filters(conn, acct):
    add(conn, acct, "2025-03-01", "UBER TRIP", -2000)
    add(conn, acct, "2025-03-10", "SALARY ACME", 50000)
    add(conn, acct, "2025-04-01", "UBER TRIP", -1500)
    assert len(transactions.list_transactions(conn, acct.id)) == 3
    assert len(transactions.list_transactions(conn, acct.id, start="2025-03-05")) == 2
    assert len(transactions.list_transactions(conn, acct.id, end="2025-03-31")) == 2
    assert len(transactions.list_transactions(conn, acct.id, category="transport")) == 2
    assert len(transactions.list_transactions(conn, acct.id, text="salary")) == 1


def test_list_is_in_date_order(conn, acct):
    add(conn, acct, "2025-03-09", "B", -1)
    add(conn, acct, "2025-03-02", "A", -1)
    days = [t.posted_on for t in transactions.list_transactions(conn, acct.id)]
    assert days == sorted(days)


def test_balance_includes_opening_and_stops_at_date(conn, acct):
    add(conn, acct, "2025-03-01", "Pay", 5000)
    add(conn, acct, "2025-03-15", "Shop", -2000)
    assert transactions.balance_as_of(conn, acct.id, "2025-03-10") == 15000.0
    assert transactions.balance_as_of(conn, acct.id, "2025-03-15") == 13000.0
    assert transactions.balance_as_of(conn, acct.id, "2025-02-01") == 10000.0


def test_balance_before_a_day(conn, acct):
    add(conn, acct, "2025-03-01", "Pay", 5000)
    assert transactions.balance_before(conn, acct.id, "2025-03-01") == 10000.0
    assert transactions.balance_before(conn, acct.id, "2025-03-02") == 15000.0


def test_running_balance(conn, acct):
    add(conn, acct, "2025-03-01", "Pay", 5000)
    add(conn, acct, "2025-03-01", "Shop", -1000)
    add(conn, acct, "2025-03-05", "Shop", -500)
    series = transactions.running_balance(conn, acct.id, "2025-03-01", "2025-03-31")
    assert series == [
        {"date": "2025-03-01", "balance": 14000.0},
        {"date": "2025-03-05", "balance": 13500.0},
    ]


def test_update_and_delete(conn, acct):
    tx = add(conn, acct, "2025-03-01", "Mystery", -100)
    changed = transactions.update_transaction(conn, tx.id, category="gifts")
    assert changed.category == "gifts"
    transactions.delete_transaction(conn, tx.id)
    with pytest.raises(LookupError):
        transactions.get_transaction(conn, tx.id)


def test_count(conn, acct):
    add(conn, acct, "2025-03-01", "A", -1)
    add(conn, acct, "2025-04-01", "B", -1)
    assert transactions.count_transactions(conn, acct.id) == 2
    assert transactions.count_transactions(conn, acct.id, start="2025-04-01") == 1
