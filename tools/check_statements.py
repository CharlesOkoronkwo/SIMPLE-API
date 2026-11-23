#!/usr/bin/env python3
"""Import the generated made-up statements and compare with manifest.json.

Run `python tools/make_statements.py` first. For each account this imports the
statements in manifest order into a scratch database (never data/ledger.db) and checks:

  1. after every statement, the balance at the end of its period equals the closing
     balance recorded in the manifest, to the kobo;
  2. after everything, the transaction count equals the number of distinct lines;
  3. re-importing every file a second time adds zero rows.

It exits 0 only if all of that holds, so it is the acceptance test for the importer work.
Layouts the importer does not know yet are reported as unsupported, not hidden.

Usage: python tools/check_statements.py [--dir samples/generated] [--verbose]
"""

import argparse
import json
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ledger import accounts, config, db, transactions  # noqa: E402
from ledger.importer import import_file  # noqa: E402


# The only place that touches money types: switch these when storage moves to integer kobo.
def to_kobo(value):
    return int(round(value * 100))


def opening_arg(kobo):
    return kobo / 100


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", default=str(ROOT / "samples" / "generated"))
    ap.add_argument("--verbose", action="store_true", help="list every failure")
    args = ap.parse_args(argv)

    base = Path(args.dir)
    try:
        manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit("no manifest.json in %s - run tools/make_statements.py first" % base)

    scratch = Path(tempfile.mkdtemp(prefix="ledger-check-")) / "check.db"
    conn = db.connect(str(scratch))

    by_layout = defaultdict(lambda: {"total": 0, "ok": 0})
    failures = []
    ids = {}
    for key, acct in manifest["accounts"].items():
        layout = acct["layout"] if acct["layout"] in config.LAYOUTS else "manual"
        ids[key] = accounts.create_account(conn, acct["name"], layout,
                                           opening_arg(acct["opening_kobo"])).id

    statements = {}
    for acct_key, acct in manifest["accounts"].items():
        for st in acct["statements"]:
            statements[st["file"]] = (acct_key, acct["layout"], st)

    for rel in manifest["import_order"]:
        acct_key, layout, st = statements[rel]
        by_layout[layout]["total"] += 1
        try:
            import_file(conn, ids[acct_key], base / rel)
        except Exception as err:  # noqa: BLE001 - report every kind of failure
            failures.append((layout, rel, "import failed: %s" % err))
            continue
        got = to_kobo(transactions.balance_as_of(conn, ids[acct_key], st["period"][1]))
        if got != st["closing_kobo"]:
            failures.append((layout, rel, "closing balance %s, expected %s (off by %s kobo)"
                             % (got, st["closing_kobo"], got - st["closing_kobo"])))
        else:
            by_layout[layout]["ok"] += 1

    dup_problems = []
    for key, acct in manifest["accounts"].items():
        count = transactions.count_transactions(conn, ids[key])
        if count != acct["unique_transactions"]:
            dup_problems.append("%s (%s): %d transactions stored, %d distinct lines expected"
                                % (key, acct["layout"], count, acct["unique_transactions"]))
    added_again = 0
    for rel in manifest["import_order"]:
        acct_key = statements[rel][0]
        try:
            added_again += import_file(conn, ids[acct_key], base / rel).rows_added
        except Exception:  # noqa: BLE001 - already reported above
            pass
    if added_again:
        dup_problems.append("re-importing every file added %d rows (expected 0)" % added_again)

    total = sum(v["total"] for v in by_layout.values())
    ok = sum(v["ok"] for v in by_layout.values())
    print("statements whose closing balance matches the manifest exactly: %d of %d" % (ok, total))
    for layout in sorted(by_layout):
        v = by_layout[layout]
        print("  %-7s %3d of %3d" % (layout, v["ok"], v["total"]))
    print("duplicate checks: %s" % ("ok" if not dup_problems else "%d problem(s)" % len(dup_problems)))
    shown = failures if args.verbose else failures[:5]
    for layout, rel, why in shown:
        print("  FAIL %s: %s" % (rel, why))
    if len(failures) > len(shown):
        print("  ... %d more (use --verbose)" % (len(failures) - len(shown)))
    for line in dup_problems[:8]:
        print("  DUP  " + line)
    passed = ok == total and not dup_problems
    print("RESULT: %s" % ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
