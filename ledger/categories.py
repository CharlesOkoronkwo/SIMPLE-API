from . import db

# Keywords seen in statement narrations. Checked in this order, first hit wins.
DEFAULT_RULES = [
    ("SALARY", "income"),
    ("PAYROLL", "income"),
    ("INTEREST", "income"),
    ("REFUND", "income"),
    ("RENT", "housing"),
    ("LANDLORD", "housing"),
    ("EKEDC", "utilities"),
    ("IKEJA ELECTRIC", "utilities"),
    ("PHCN", "utilities"),
    ("DSTV", "utilities"),
    ("GOTV", "utilities"),
    ("WATER BOARD", "utilities"),
    ("MTN", "airtime"),
    ("AIRTEL", "airtime"),
    ("GLO", "airtime"),
    ("9MOBILE", "airtime"),
    ("AIRTIME", "airtime"),
    ("DATA BUNDLE", "airtime"),
    ("SHOPRITE", "groceries"),
    ("SPAR", "groceries"),
    ("MARKET", "groceries"),
    ("UBER", "transport"),
    ("BOLT", "transport"),
    ("FUEL", "transport"),
    ("TOTAL ENERGIES", "transport"),
    ("MOBIL", "transport"),
    ("DOMINOS", "eating out"),
    ("KFC", "eating out"),
    ("CHICKEN REPUBLIC", "eating out"),
    ("RESTAURANT", "eating out"),
    ("PHARMACY", "health"),
    ("HOSPITAL", "health"),
    ("STAMP DUTY", "bank charges"),
    ("SMS ALERT", "bank charges"),
    ("VAT", "bank charges"),
    ("MAINTENANCE FEE", "bank charges"),
    ("ATM", "cash"),
    ("WITHDRAWAL", "cash"),
    ("TRANSFER TO", "transfers"),
    ("TRANSFER FROM", "transfers"),
    ("NIP", "transfers"),
]

FALLBACK = "uncategorised"


def custom_rules(conn):
    rows = db.many(conn, "SELECT keyword, category FROM category_rules ORDER BY id")
    return [(r["keyword"], r["category"]) for r in rows]


def categorize(conn, description):
    """Pick a category for a narration. Our own rules come before the defaults."""
    text = (description or "").upper()
    for keyword, category in custom_rules(conn):
        if keyword.upper() in text:
            return category
    for keyword, category in DEFAULT_RULES:
        if keyword in text:
            return category
    return FALLBACK


def add_rule(conn, keyword, category):
    keyword = (keyword or "").strip().upper()
    category = (category or "").strip().lower()
    if not keyword or not category:
        raise ValueError("keyword and category are both required")
    conn.execute(
        "INSERT INTO category_rules (keyword, category) VALUES (?, ?) "
        "ON CONFLICT(keyword) DO UPDATE SET category = excluded.category",
        (keyword, category),
    )
    conn.commit()


def remove_rule(conn, keyword):
    conn.execute("DELETE FROM category_rules WHERE keyword = ?", ((keyword or "").upper(),))
    conn.commit()


def list_rules(conn):
    return [{"keyword": k, "category": c, "builtin": False} for k, c in custom_rules(conn)] + [
        {"keyword": k, "category": c, "builtin": True} for k, c in DEFAULT_RULES
    ]


def recategorize(conn, account_id=None, only_uncategorised=True):
    """Run the rules again over stored transactions. Returns how many changed."""
    sql = "SELECT id, description, category FROM transactions"
    params = []
    clauses = []
    if account_id is not None:
        clauses.append("account_id = ?")
        params.append(account_id)
    if only_uncategorised:
        clauses.append("(category IS NULL OR category = ?)")
        params.append(FALLBACK)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    changed = 0
    for row in db.many(conn, sql, params):
        new = categorize(conn, row["description"])
        if new != row["category"]:
            conn.execute("UPDATE transactions SET category = ? WHERE id = ?", (new, row["id"]))
            changed += 1
    conn.commit()
    return changed
