from . import accounts, db
from .money import round_kobo
from .summary import spending_by_category


def set_budget(conn, account_id, category, monthly_cap):
    accounts.get_account(conn, account_id)
    category = (category or "").strip().lower()
    if not category:
        raise ValueError("category is required")
    cap = float(monthly_cap)
    if cap <= 0:
        raise ValueError("monthly cap must be more than zero")
    conn.execute(
        "INSERT INTO budgets (account_id, category, monthly_cap) VALUES (?, ?, ?) "
        "ON CONFLICT(account_id, category) DO UPDATE SET monthly_cap = excluded.monthly_cap",
        (account_id, category, cap),
    )
    conn.commit()


def remove_budget(conn, account_id, category):
    conn.execute(
        "DELETE FROM budgets WHERE account_id = ? AND category = ?",
        (account_id, (category or "").strip().lower()),
    )
    conn.commit()


def list_budgets(conn, account_id):
    rows = db.many(
        conn,
        "SELECT category, monthly_cap FROM budgets WHERE account_id = ? ORDER BY category",
        (account_id,),
    )
    return [{"category": r["category"], "monthly_cap": r["monthly_cap"]} for r in rows]


def budget_status(conn, account_id, month):
    """For each budget: how much was spent this month and what is left."""
    spent = {c["category"]: c["spent"] for c in spending_by_category(conn, account_id, month)}
    status = []
    for budget in list_budgets(conn, account_id):
        used = spent.get(budget["category"], 0.0)
        cap = budget["monthly_cap"]
        status.append(
            {
                "category": budget["category"],
                "monthly_cap": cap,
                "spent": used,
                "remaining": round_kobo(cap - used),
                "percent_used": round(used / cap * 100, 1),
                "over": used > cap,
            }
        )
    return status
