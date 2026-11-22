"""Command line tool for the ledger.

    python -m ledger.cli accounts
    python -m ledger.cli import 1 samples/statements/gtb-2025-03.csv
    python -m ledger.cli balance 1 --as-of 2025-03-31

The database is data/ledger.db unless LEDGER_DB is set.
"""

import argparse
import sys

from . import accounts, budgets, categories, config, db, export, summary, transactions
from .dates import today_iso
from .importer import import_file, import_history
from .money import format_naira


def cmd_init(args, conn):
    print("database ready at %s" % config.db_path())


def cmd_accounts(args, conn):
    rows = accounts.list_accounts(conn)
    if not rows:
        print("no accounts yet")
    for a in rows:
        print("%d  %-22s %-7s opening %s" % (a.id, a.name, a.layout, format_naira(a.opening_balance)))


def cmd_add_account(args, conn):
    account = accounts.create_account(conn, args.name, args.layout, args.opening)
    print("created account %d (%s)" % (account.id, account.name))


def cmd_import(args, conn):
    result = import_file(conn, args.account, args.file, layout_name=args.layout)
    print("%s: read %d, added %d, skipped %d" % (
        result.filename, result.rows_read, result.rows_added, result.rows_skipped))
    if args.verbose:
        for problem in result.problems or []:
            print("  " + problem)


def cmd_imports(args, conn):
    for row in import_history(conn, args.account):
        print("%s  %-24s read %3d  added %3d  skipped %d" % (
            row["imported_at"], row["filename"], row["rows_read"],
            row["rows_added"], row["rows_skipped"]))


def cmd_balance(args, conn):
    as_of = args.as_of or today_iso()
    value = transactions.balance_as_of(conn, args.account, as_of)
    print("balance on %s: %s" % (as_of, format_naira(value)))


def cmd_transactions(args, conn):
    rows = transactions.list_transactions(
        conn, args.account, start=args.start, end=args.end,
        category=args.category, text=args.search, limit=args.limit)
    for tx in rows:
        print("%s  %14s  %-14s %s" % (
            tx.posted_on, format_naira(tx.amount), tx.category or "-", tx.description))
    print("%d shown" % len(rows))


def cmd_summary(args, conn):
    data = summary.month_summary(conn, args.account, args.month)
    print("summary for %s" % data["month"])
    print("  opening balance : %s" % format_naira(data["opening_balance"]))
    print("  money in        : %s" % format_naira(data["money_in"]))
    print("  money out       : %s" % format_naira(data["money_out"]))
    print("  closing balance : %s" % format_naira(data["closing_balance"]))
    print("  transactions    : %d" % data["transaction_count"])
    for item in data["by_category"][:8]:
        print("    %-14s %s" % (item["category"], format_naira(item["spent"])))


def cmd_budgets(args, conn):
    if args.set_category:
        budgets.set_budget(conn, args.account, args.set_category, args.cap)
    for row in budgets.budget_status(conn, args.account, args.month):
        flag = "OVER" if row["over"] else "ok"
        print("%-14s %s of %s (%s%%) %s" % (
            row["category"], format_naira(row["spent"]),
            format_naira(row["monthly_cap"]), row["percent_used"], flag))


def cmd_export(args, conn):
    count = export.export_csv(conn, args.account, sys.stdout, args.start, args.end)
    print("%d rows written" % count, file=sys.stderr)


def cmd_rules(args, conn):
    if args.add:
        categories.add_rule(conn, args.add[0], args.add[1])
    if args.recategorize:
        print("%d changed" % categories.recategorize(conn))
        return
    for rule in categories.list_rules(conn):
        if not rule["builtin"]:
            print("%-20s -> %s" % (rule["keyword"], rule["category"]))


def build_parser():
    parser = argparse.ArgumentParser(prog="ledger", description="Naira transaction tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create the database if needed").set_defaults(func=cmd_init)
    sub.add_parser("accounts", help="list accounts").set_defaults(func=cmd_accounts)

    p = sub.add_parser("add-account", help="create an account")
    p.add_argument("name")
    p.add_argument("--layout", default="manual", choices=config.LAYOUTS)
    p.add_argument("--opening", type=float, default=0.0)
    p.set_defaults(func=cmd_add_account)

    p = sub.add_parser("import", help="import a bank statement CSV")
    p.add_argument("account", type=int)
    p.add_argument("file")
    p.add_argument("--layout", choices=config.LAYOUTS)
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("imports", help="show import history")
    p.add_argument("account", type=int)
    p.set_defaults(func=cmd_imports)

    p = sub.add_parser("balance", help="balance on a date")
    p.add_argument("account", type=int)
    p.add_argument("--as-of")
    p.set_defaults(func=cmd_balance)

    p = sub.add_parser("transactions", help="list transactions")
    p.add_argument("account", type=int)
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--category")
    p.add_argument("--search")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_transactions)

    p = sub.add_parser("summary", help="monthly summary")
    p.add_argument("account", type=int)
    p.add_argument("month", help="for example 2025-03")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("budgets", help="show or set budgets")
    p.add_argument("account", type=int)
    p.add_argument("month")
    p.add_argument("--set-category")
    p.add_argument("--cap", type=float)
    p.set_defaults(func=cmd_budgets)

    p = sub.add_parser("export", help="write transactions as CSV to stdout")
    p.add_argument("account", type=int)
    p.add_argument("--start")
    p.add_argument("--end")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("rules", help="custom category rules")
    p.add_argument("--add", nargs=2, metavar=("KEYWORD", "CATEGORY"))
    p.add_argument("--recategorize", action="store_true")
    p.set_defaults(func=cmd_rules)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = db.connect()
    try:
        args.func(args, conn)
    except (ValueError, LookupError) as err:
        print("error: %s" % err, file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
