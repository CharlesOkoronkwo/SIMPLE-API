import pytest

from ledger import accounts, budgets, summary, transactions


@pytest.fixture
def acct(conn):
    a = accounts.create_account(conn, "Main", "manual", 100000)
    add = lambda d, desc, amt: transactions.add_transaction(conn, a.id, d, desc, amt)
    add("2025-02-10", "UBER TRIP", -4000)
    add("2025-02-20", "SHOPRITE", -20000)
    add("2025-03-02", "SALARY ACME", 300000)
    add("2025-03-05", "SHOPRITE", -35000)
    add("2025-03-09", "UBER TRIP", -2500)
    add("2025-03-30", "UBER TRIP", -1500)
    return a


def test_month_summary_numbers(conn, acct):
    data = summary.month_summary(conn, acct.id, "2025-03")
    assert data["opening_balance"] == 76000.0
    assert data["money_in"] == 300000.0
    assert data["money_out"] == 39000.0
    assert data["net"] == 261000.0
    assert data["closing_balance"] == 337000.0
    assert data["transaction_count"] == 4


def test_summary_by_category(conn, acct):
    data = summary.month_summary(conn, acct.id, "2025-03")
    by_name = {c["category"]: c["spent"] for c in data["by_category"]}
    assert by_name == {"groceries": 35000.0, "transport": 4000.0}


def test_top_payees(conn, acct):
    top = summary.top_payees(conn, acct.id, "2025-03")
    assert top[0] == {"description": "SHOPRITE", "spent": 35000.0}


def test_empty_month(conn, acct):
    data = summary.month_summary(conn, acct.id, "2024-01")
    assert data["transaction_count"] == 0
    assert data["closing_balance"] == 100000.0


def test_monthly_series(conn, acct):
    series = summary.monthly_series(conn, acct.id, "2025-03", count=2)
    assert [s["month"] for s in series] == ["2025-02", "2025-03"]
    assert series[0]["money_out"] == 24000.0


def test_compare_with_previous_month(conn, acct):
    rows = {r["category"]: r for r in summary.compare_with_previous(conn, acct.id, "2025-03")}
    assert rows["groceries"]["change"] == 15000.0
    assert rows["transport"]["change"] == 0.0


def test_daily_totals_and_largest(conn, acct):
    days = summary.daily_totals(conn, acct.id, "2025-03")
    assert days[0] == {"date": "2025-03-02", "net": 300000.0, "count": 1}
    assert summary.largest_transactions(conn, acct.id, "2025-03", limit=1)[0]["amount"] == 300000.0


def test_budget_status(conn, acct):
    budgets.set_budget(conn, acct.id, "groceries", 30000)
    budgets.set_budget(conn, acct.id, "transport", 10000)
    status = {b["category"]: b for b in budgets.budget_status(conn, acct.id, "2025-03")}
    assert status["groceries"]["over"] is True
    assert status["groceries"]["remaining"] == -5000.0
    assert status["transport"]["over"] is False
    assert status["transport"]["percent_used"] == 40.0


def test_budget_needs_a_positive_cap(conn, acct):
    with pytest.raises(ValueError):
        budgets.set_budget(conn, acct.id, "groceries", 0)
