from ledger import accounts, categories, transactions


def test_default_rules(conn):
    assert categories.categorize(conn, "MTN AIRTIME TOPUP") == "airtime"
    assert categories.categorize(conn, "salary payment acme") == "income"
    assert categories.categorize(conn, "something odd") == "uncategorised"


def test_custom_rule_wins_over_default(conn):
    categories.add_rule(conn, "kfc", "treats")
    assert categories.categorize(conn, "KFC YABA") == "treats"


def test_adding_a_rule_twice_replaces_it(conn):
    categories.add_rule(conn, "tola", "family")
    categories.add_rule(conn, "tola", "friends")
    assert categories.categorize(conn, "NIP TOLA") == "friends"


def test_remove_rule(conn):
    categories.add_rule(conn, "tola", "family")
    categories.remove_rule(conn, "tola")
    assert categories.categorize(conn, "NIP TOLA") == "transfers"


def test_recategorize_only_touches_uncategorised(conn):
    acct = accounts.create_account(conn, "Main", "manual")
    tx = transactions.add_transaction(conn, acct.id, "2025-03-01", "CHOPS BUKA", -900)
    kept = transactions.add_transaction(conn, acct.id, "2025-03-02", "KFC", -900, category="mine")
    categories.add_rule(conn, "CHOPS", "eating out")
    assert categories.recategorize(conn) == 1
    assert transactions.get_transaction(conn, tx.id).category == "eating out"
    assert transactions.get_transaction(conn, kept.id).category == "mine"
