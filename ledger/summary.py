from . import accounts, db, transactions
from .dates import last_months, month_bounds, previous_month
from .money import round_kobo


def month_totals(conn, account_id, month):
    """Money in, money out and number of rows for one month."""
    start, end = month_bounds(month)
    row = db.one(
        conn,
        "SELECT "
        " COALESCE(SUM(CASE WHEN amount > 0 THEN amount END), 0) AS money_in, "
        " COALESCE(SUM(CASE WHEN amount < 0 THEN amount END), 0) AS money_out, "
        " COUNT(*) AS n "
        "FROM transactions WHERE account_id = ? AND posted_on BETWEEN ? AND ?",
        (account_id, start, end),
    )
    return {
        "money_in": round_kobo(row["money_in"]),
        "money_out": round_kobo(-row["money_out"]),
        "count": row["n"],
    }


def spending_by_category(conn, account_id, month):
    start, end = month_bounds(month)
    rows = db.many(
        conn,
        "SELECT COALESCE(category, 'uncategorised') AS category, "
        "       SUM(-amount) AS spent, COUNT(*) AS n "
        "FROM transactions "
        "WHERE account_id = ? AND amount < 0 AND posted_on BETWEEN ? AND ? "
        "GROUP BY category ORDER BY spent DESC",
        (account_id, start, end),
    )
    return [
        {"category": r["category"], "spent": round_kobo(r["spent"]), "count": r["n"]}
        for r in rows
    ]


def top_payees(conn, account_id, month, limit=5):
    start, end = month_bounds(month)
    rows = db.many(
        conn,
        "SELECT description, SUM(-amount) AS spent FROM transactions "
        "WHERE account_id = ? AND amount < 0 AND posted_on BETWEEN ? AND ? "
        "GROUP BY description ORDER BY spent DESC LIMIT ?",
        (account_id, start, end, limit),
    )
    return [{"description": r["description"], "spent": round_kobo(r["spent"])} for r in rows]


def month_summary(conn, account_id, month):
    """The numbers shown on the dashboard for one month."""
    accounts.get_account(conn, account_id)
    start, end = month_bounds(month)
    totals = month_totals(conn, account_id, month)
    opening = transactions.balance_before(conn, account_id, start)
    closing = transactions.balance_as_of(conn, account_id, end)
    return {
        "account_id": account_id,
        "month": month,
        "opening_balance": opening,
        "money_in": totals["money_in"],
        "money_out": totals["money_out"],
        "net": round_kobo(totals["money_in"] - totals["money_out"]),
        "closing_balance": closing,
        "transaction_count": totals["count"],
        "by_category": spending_by_category(conn, account_id, month),
        "top_payees": top_payees(conn, account_id, month),
    }


def monthly_series(conn, account_id, month, count=6):
    """Money in and out for the last few months, oldest first."""
    series = []
    for m in last_months(month, count):
        totals = month_totals(conn, account_id, m)
        series.append({"month": m, "money_in": totals["money_in"], "money_out": totals["money_out"]})
    return series


def compare_with_previous(conn, account_id, month):
    """How spending this month differs from last month, per category."""
    now = {c["category"]: c["spent"] for c in spending_by_category(conn, account_id, month)}
    before = {
        c["category"]: c["spent"]
        for c in spending_by_category(conn, account_id, previous_month(month))
    }
    rows = []
    for name in sorted(set(now) | set(before)):
        this_month = now.get(name, 0.0)
        last_month = before.get(name, 0.0)
        rows.append(
            {
                "category": name,
                "this_month": this_month,
                "last_month": last_month,
                "change": round_kobo(this_month - last_month),
            }
        )
    rows.sort(key=lambda r: abs(r["change"]), reverse=True)
    return rows


def daily_totals(conn, account_id, month):
    start, end = month_bounds(month)
    rows = db.many(
        conn,
        "SELECT posted_on, SUM(amount) AS net, COUNT(*) AS n FROM transactions "
        "WHERE account_id = ? AND posted_on BETWEEN ? AND ? "
        "GROUP BY posted_on ORDER BY posted_on",
        (account_id, start, end),
    )
    return [{"date": r["posted_on"], "net": round_kobo(r["net"]), "count": r["n"]} for r in rows]


def largest_transactions(conn, account_id, month, limit=5):
    start, end = month_bounds(month)
    rows = db.many(
        conn,
        "SELECT posted_on, description, amount FROM transactions "
        "WHERE account_id = ? AND posted_on BETWEEN ? AND ? "
        "ORDER BY ABS(amount) DESC LIMIT ?",
        (account_id, start, end, limit),
    )
    return [
        {"date": r["posted_on"], "description": r["description"], "amount": round_kobo(r["amount"])}
        for r in rows
    ]
