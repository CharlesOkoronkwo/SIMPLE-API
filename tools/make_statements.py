#!/usr/bin/env python3
"""Generate a large set of MADE-UP bank statements with known closing balances.

Everything is invented from a fixed random seed. Money is integer kobo throughout, so
the expected balances are exact and do not depend on the Ledger importer (this script
imports nothing from `ledger`). Output:

    samples/generated/<account>/<file>.csv
    samples/generated/manifest.json     expected opening/closing balance of every file

Four layouts (see docs/STATEMENT_FORMATS.md):
    bank_a  Debit/Credit columns, dd/mm/yyyy, bracketed debit = reversal (money back)
    bank_b  one signed Amount (brackets = out), ISO dates, bank reference, closing row only
    bank_c  signed Amount with minus sign, dd-Mon-yyyy, running balance, B/F and C/F rows
    bank_d  semicolon separated, Dr/Cr column, naira sign, dd.mm.yyyy, BOM and CRLF

Some months also get a part-month export (an early download of the same month), whose
lines are an exact subset of the full-month file, and some get a "tail" export (mid-month
to month end) that overlaps the other way. Both test duplicate handling; tails also start
on a day above 12, so their dates are unambiguous.

Usage: python tools/make_statements.py [--out DIR] [--seed N] [--accounts 8] [--months 26]
"""

import argparse
import calendar
import csv
import io
import json
import random
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
NAMES = ["ADA", "KEMI", "BALA", "CHIDI", "SEUN", "AMINA", "NGOZI", "EMEKA", "TUNDE", "ZAINAB"]
LAYOUT_CYCLE = ["bank_a", "bank_b", "bank_c", "bank_d"]
START = (2024, 1)

# (narration, low NGN, high NGN, weight, whole_naira_only)
DEBITS = [
    ("POS PURCHASE SHOPRITE", 3000, 25000, 6, False),
    ("POS PURCHASE SPAR", 2000, 15000, 3, False),
    ("UBER TRIP", 900, 6000, 6, False),
    ("BOLT TRIP", 800, 5000, 3, False),
    ("MTN AIRTIME", 500, 5000, 5, True),
    ("KFC", 1500, 6000, 3, False),
    ("CHICKEN REPUBLIC", 1200, 5000, 3, False),
    ("DOMINOS PIZZA", 3000, 9000, 1, False),
    ("ATM WITHDRAWAL", 5000, 50000, 2, True),
    ("NIP TRANSFER TO {name}", 2000, 40000, 4, False),
    ("FUEL TOTAL ENERGIES", 8000, 30000, 2, False),
    ("MARKET PURCHASE", 3000, 20000, 2, False),
    ("PHARMACY", 1500, 12000, 1, False),
]
CREDIT_TRANSFER = ("NIP TRANSFER FROM {name}", 5000, 60000)
STAMP_THRESHOLD = 10_000 * 100  # credits of NGN 10,000 or more attract a NGN 50 stamp duty
STAMP = 50 * 100


# --------------------------------------------------------------------------- formatting
def fmt(kobo, commas=True):
    """Integer kobo -> '1,234.56' (no sign)."""
    kobo = abs(kobo)
    naira, k = divmod(kobo, 100)
    return ("{:,}".format(naira) if commas else str(naira)) + ".%02d" % k


def parse_money(text):
    """'₦(1,234.56)' / '-1,234.56' / '1234.5' -> signed integer kobo. Exact, no floats."""
    s = text.strip().replace("₦", "").replace(",", "")
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = s.strip("()-")
    naira, _, frac = s.partition(".")
    kobo = int(naira or 0) * 100 + int((frac + "00")[:2])
    return -kobo if neg else kobo


def fmt_date(layout, d):
    return {
        "bank_a": "%02d/%02d/%d" % (d.day, d.month, d.year),
        "bank_b": d.isoformat(),
        "bank_c": "%02d-%s-%d" % (d.day, MON[d.month - 1], d.year),
        "bank_d": "%02d.%02d.%d" % (d.day, d.month, d.year),
    }[layout]


def parse_date(layout, text):
    if layout == "bank_a":
        dd, mm, yy = text.split("/")
    elif layout == "bank_b":
        yy, mm, dd = text.split("-")
    elif layout == "bank_c":
        dd, mon, yy = text.split("-")
        mm = MON.index(mon) + 1
    else:
        dd, mm, yy = text.split(".")
    return date(int(yy), int(mm), int(dd))


# --------------------------------------------------------------------------- generation
def pick(rng, table):
    return rng.choices(table, weights=[t[3] for t in table])[0]


def make_account(rng, index, layout):
    salary = rng.choice([250_000, 350_000, 450_000, 600_000, 1_250_000])
    return {
        "key": "%s%d" % (layout[-1], index // len(LAYOUT_CYCLE) + 1),
        "layout": layout,
        "name": "Demo %s %d" % (layout, index // len(LAYOUT_CYCLE) + 1),
        "opening_kobo": rng.randint(150_000, 900_000) * 100 + rng.randint(0, 99),
        "salary": salary * 100,
        "rent": rng.choice([60_000, 90_000, 120_000]) * 100,
        "scale": salary / 450_000,
        "seq": 0,
    }


def gen_month(rng, acct, balance, year, month):
    """Rows for one calendar month. Returns (rows, closing balance, counts)."""
    days = calendar.monthrange(year, month)[1]
    plan = defaultdict(list)  # day -> [(narration, signed kobo, flags)]
    plan[rng.randint(1, 3)].append(("TRANSFER TO LANDLORD RENT", -acct["rent"], {}))
    plan[rng.randint(24, 28)].append(("SALARY PAYMENT DEMO EMPLOYER LTD", acct["salary"], {"stamp": True}))
    if rng.random() < 0.7:
        plan[rng.randint(5, 12)].append(("DSTV SUBSCRIPTION", -21_000 * 100, {}))
    if rng.random() < 0.8:
        plan[rng.randint(3, 20)].append(("EKEDC PREPAID ELECTRICITY", -rng.randint(5_000, 25_000) * 100, {}))
    plan[days].append(("ACCOUNT MAINTENANCE FEE", -1_000 * 100, {}))
    plan[days].append(("INTEREST ON BALANCE", rng.randint(1, 90_000), {}))
    for _ in range(rng.randint(32, 62)):
        day = rng.randint(1, days)
        if rng.random() < 0.12:
            text, lo, hi = CREDIT_TRANSFER
            amount = rng.randint(lo, hi) * 100 + rng.randint(0, 99)
            plan[day].append((text.format(name=rng.choice(NAMES)), amount, {"stamp": True}))
            continue
        text, lo, hi, _, whole = pick(rng, DEBITS)
        lo, hi = int(lo * acct["scale"]), max(int(hi * acct["scale"]), int(lo * acct["scale"]) + 1)
        naira = rng.randint(lo, hi)
        kobo = 0 if whole else rng.randint(0, 99)
        amount = -(naira * 100 + (kobo if not whole else 0))
        flags = {"twin": rng.random() < 0.006 and amount > -10_000 * 100,
                 "may_reverse": text.startswith("NIP TRANSFER TO")}
        plan[day].append((text.format(name=rng.choice(NAMES)), amount, flags))

    rows, pending = [], defaultdict(list)
    counts = {"reversals": 0, "twins": 0}

    def add(day, narration, signed, reversal=False):
        nonlocal balance
        if signed < 0 and balance + signed < 0:
            return False  # never overdraw: skip this line
        balance += signed
        acct["seq"] += 1
        rows.append({"date": date(year, month, day), "narration": narration, "kobo": signed,
                     "balance": balance, "seq": acct["seq"], "reversal": reversal})
        return True

    for day in range(1, days + 1):
        for narration, signed, flags in pending.pop(day, []):
            if add(day, narration, signed, reversal=True):
                counts["reversals"] += 1
        for narration, signed, flags in plan.get(day, []):
            if not add(day, narration, signed):
                continue
            if flags.get("twin") and add(day, narration, signed):
                counts["twins"] += 1
            if flags.get("may_reverse") and day < days and rng.random() < 0.05:
                pending[min(days, day + rng.randint(1, 5))].append(("REVERSAL " + narration, -signed, {}))
            if flags.get("stamp") and signed >= STAMP_THRESHOLD:
                add(day, "STAMP DUTY", -STAMP)
    for day, items in pending.items():  # reversals scheduled past the month end land on its last day
        for narration, signed, _ in items:
            if add(days, narration, signed, reversal=True):
                counts["reversals"] += 1
    rows.sort(key=lambda r: (r["date"], r["seq"]))
    return rows, balance, counts


# --------------------------------------------------------------------------- rendering
def render(layout, rows, opening, closing, rng):
    """CSV text for one statement."""
    out = io.StringIO()
    if layout == "bank_d":
        w = csv.writer(out, delimiter=";", lineterminator="\r\n")
    else:
        w = csv.writer(out, lineterminator="\r\n" if rng.random() < 0.15 else "\n")
    if layout == "bank_a":
        w.writerow(["Date", "Description", "Debit", "Credit", "Balance"])
        w.writerow(["", "Opening Balance", "", "", fmt(opening)])
        for r in rows:
            if r["reversal"]:
                cells = ["(%s)" % fmt(r["kobo"]), ""]  # bracketed debit: money came back
            elif r["kobo"] < 0:
                cells = [fmt(r["kobo"], commas=r["kobo"] <= -100_000 or rng.random() < 0.8), ""]
            else:
                cells = ["", fmt(r["kobo"])]
            w.writerow([fmt_date(layout, r["date"]), r["narration"]] + cells + [fmt(r["balance"])])
        w.writerow(["", "Closing Balance", "", "", fmt(closing)])
    elif layout == "bank_b":
        w.writerow(["Posted", "Narration", "Amount", "Ref"])
        for r in rows:
            amount = fmt(r["kobo"], commas=abs(r["kobo"]) >= 100_000 and rng.random() < 0.7)
            amount = "(%s)" % amount if r["kobo"] < 0 else amount
            w.writerow([fmt_date(layout, r["date"]), r["narration"], amount, r["ref"]])
        w.writerow(["", "Closing balance", fmt(closing), ""])
    elif layout == "bank_c":
        w.writerow(["Value Date", "Narrative", "Amount (NGN)", "Balance (NGN)"])
        w.writerow(["", "BALANCE B/F", "", fmt(opening)])
        for r in rows:
            sign = "-" if r["kobo"] < 0 else ""
            w.writerow([fmt_date(layout, r["date"]), r["narration"], sign + fmt(r["kobo"]), fmt(r["balance"])])
        w.writerow(["", "BALANCE C/F", "", fmt(closing)])
    else:
        w.writerow(["Date", "Ref", "Narration", "Dr/Cr", "Amount", "Balance"])
        w.writerow(["", "", "Opening balance", "", "", "₦" + fmt(opening)])
        for r in rows:
            w.writerow([fmt_date(layout, r["date"]), r["ref"], r["narration"],
                        "DR" if r["kobo"] < 0 else "CR", "₦" + fmt(r["kobo"]), "₦" + fmt(r["balance"])])
        w.writerow(["", "", "Closing balance", "", "", "₦" + fmt(closing)])
    return out.getvalue()


def write_file(path, layout, text):
    # bank_d exports carry a byte order mark; the others only sometimes do
    bom = layout == "bank_d" or (layout == "bank_a" and hash_bit(path.name))
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
    return bom


def hash_bit(text):
    return sum(map(ord, text)) % 7 == 0


# --------------------------------------------------------------------------- verification
def reread(layout, path):
    """Independent reader: returns (opening or None, closing, [(date, narration, kobo, balance|None)])."""
    text = path.read_bytes().decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text), delimiter=";" if layout == "bank_d" else ",")
    next(reader)
    opening, closing, rows = None, None, []
    for cells in reader:
        if not any(cells):
            continue
        if layout == "bank_a":
            d, narr, debit, credit, bal = cells
            if not d:
                if narr.startswith("Opening"):
                    opening = parse_money(bal)
                else:
                    closing = parse_money(bal)
                continue
            if debit.startswith("("):
                kobo = abs(parse_money(debit))  # bracketed debit = reversal = money in
            elif debit:
                kobo = -parse_money(debit)
            else:
                kobo = parse_money(credit)
            rows.append((parse_date(layout, d), narr, kobo, parse_money(bal)))
        elif layout == "bank_b":
            d, narr, amount, _ref = cells
            if not d:
                closing = parse_money(amount)
                continue
            rows.append((parse_date(layout, d), narr, parse_money(amount), None))
        elif layout == "bank_c":
            d, narr, amount, bal = cells
            if not d:
                if narr.endswith("B/F"):
                    opening = parse_money(bal)
                else:
                    closing = parse_money(bal)
                continue
            rows.append((parse_date(layout, d), narr, parse_money(amount), parse_money(bal)))
        else:
            d, _ref, narr, drcr, amount, bal = cells
            if not d:
                if narr.startswith("Opening"):
                    opening = parse_money(bal)
                else:
                    closing = parse_money(bal)
                continue
            kobo = abs(parse_money(amount)) * (-1 if drcr == "DR" else 1)
            rows.append((parse_date(layout, d), narr, kobo, parse_money(bal)))
    return opening, closing, rows


def verify(out, manifest, truth):
    """Re-read every file we wrote and check it against what we meant to write."""
    problems = []
    for acct_key, acct in manifest["accounts"].items():
        carried = acct["opening_kobo"]
        for st in acct["statements"]:
            try:
                opening, closing, rows = reread(acct["layout"], out / st["file"])
            except (ValueError, IndexError) as err:
                problems.append("%s: cannot be re-read (%s)" % (st["file"], err))
                continue
            want = truth[st["file"]]
            got = [(r[0], r[1], r[2]) for r in rows]
            if got != [(r["date"], r["narration"], r["kobo"]) for r in want]:
                problems.append("%s: lines differ from what was generated" % st["file"])
            if closing != st["closing_kobo"]:
                problems.append("%s: closing row %s != %s" % (st["file"], closing, st["closing_kobo"]))
            if opening is not None and opening != st["opening_kobo"]:
                problems.append("%s: opening row mismatch" % st["file"])
            if st["kind"] != "tail" and st["opening_kobo"] != carried:
                problems.append("%s: does not chain from previous closing" % st["file"])
            if st["opening_kobo"] + sum(r[2] for r in rows) != st["closing_kobo"]:
                problems.append("%s: opening + lines != closing" % st["file"])
            if any(r[3] is not None for r in rows):
                bal = st["opening_kobo"]
                for r in rows:
                    bal += r[2]
                    if bal != r[3]:
                        problems.append("%s: running balance breaks at %s" % (st["file"], r[0]))
                        break
            carried = st["closing_kobo"] if st["kind"] == "full" else carried
    return problems


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "samples" / "generated"))
    ap.add_argument("--seed", type=int, default=20250101)
    ap.add_argument("--accounts", type=int, default=8)
    ap.add_argument("--months", type=int, default=26)
    args = ap.parse_args(argv)
    if args.accounts < len(LAYOUT_CYCLE):
        ap.error("--accounts must be at least %d so every layout appears" % len(LAYOUT_CYCLE))

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rng = random.Random(args.seed)

    manifest = {"seed": args.seed, "currency": "NGN", "unit": "kobo (integers)",
                "note": "All data is made up.", "import_order": [], "accounts": {}}
    truth = {}
    for index in range(args.accounts):
        acct = make_account(rng, index, LAYOUT_CYCLE[index % len(LAYOUT_CYCLE)])
        folder = out / acct["key"]
        folder.mkdir()
        balance = acct["opening_kobo"]
        record = {"name": acct["name"], "layout": acct["layout"], "opening_kobo": balance,
                  "statements": []}
        unique_rows = 0
        year, month = START
        for _ in range(args.months):
            month_open = balance
            rows, balance, counts = gen_month(rng, acct, balance, year, month)
            for r in rows:
                r["ref"] = ("FT%sB%04d" % (r["date"].strftime("%y%m%d"), r["seq"]) if acct["layout"] == "bank_b"
                            else "D%s-%04d" % (r["date"].strftime("%y%m%d"), r["seq"]))
            unique_rows += len(rows)
            tag = "%04d-%02d" % (year, month)
            versions = [("full", "%s-%s.csv" % (acct["key"], tag), rows, month_open, balance, None)]
            if rng.random() < 0.12:  # an early, part-month download of the same month
                cut = rng.randint(8, 20)
                part = [r for r in rows if r["date"].day <= cut]
                if len(part) >= 3:
                    part_close = part[-1]["balance"]
                    versions.insert(0, ("partial", "%s-%s-to-%02dth.csv" % (acct["key"], tag, cut),
                                        part, month_open, part_close, cut))
            if rng.random() < 0.08:  # a later download from mid-month to the end
                cut = rng.randint(13, 22)
                tail = [r for r in rows if r["date"].day >= cut]
                if len(tail) >= 3:
                    first = len(rows) - len(tail)
                    tail_open = rows[first - 1]["balance"] if first else month_open
                    versions.append(("tail", "%s-%s-from-%02dth.csv" % (acct["key"], tag, cut),
                                     tail, tail_open, balance, cut))
            for kind, name, body, op, cl, cut in versions:
                srng = random.Random("%s-%s" % (args.seed, name))
                path = folder / name
                bom = write_file(path, acct["layout"], render(acct["layout"], body, op, cl, srng))
                first = [r["date"].day for r in body[:5]]
                traits = []
                if counts["reversals"] and any(r["reversal"] for r in body):
                    traits.append("reversal")
                if any(body[i]["narration"] == body[i + 1]["narration"] and body[i]["kobo"] == body[i + 1]["kobo"]
                       and body[i]["date"] == body[i + 1]["date"] for i in range(len(body) - 1)):
                    traits.append("identical_lines_same_day")
                if acct["layout"] in ("bank_a", "bank_d") and all(d <= 12 for d in first) \
                        and any(r["date"].day > 12 for r in body[5:]):
                    traits.append("ambiguous_date_head")
                if kind != "full":
                    traits.append(kind + "_export")
                if bom:
                    traits.append("bom")
                last_day = calendar.monthrange(year, month)[1]
                period_start = date(year, month, cut if kind == "tail" else 1)
                period_end = date(year, month, cut if kind == "partial" else last_day)
                rel = "%s/%s" % (acct["key"], name)
                record["statements"].append({
                    "file": rel, "kind": kind, "period": [period_start.isoformat(), period_end.isoformat()],
                    "opening_kobo": op, "closing_kobo": cl, "rows": len(body), "traits": traits})
                truth[rel] = body
                manifest["import_order"].append(rel)
            month += 1
            if month == 13:
                year, month = year + 1, 1
        record["final_balance_kobo"] = balance
        record["unique_transactions"] = unique_rows
        manifest["accounts"][acct["key"]] = record

    statements = [s for a in manifest["accounts"].values() for s in a["statements"]]
    manifest["totals"] = {
        "statements": len(statements),
        "layouts": sorted({a["layout"] for a in manifest["accounts"].values()}),
        "partial_exports": sum(s["kind"] == "partial" for s in statements),
        "tail_exports": sum(s["kind"] == "tail" for s in statements),
        "with_reversals": sum("reversal" in s["traits"] for s in statements),
        "with_ambiguous_date_head": sum("ambiguous_date_head" in s["traits"] for s in statements),
        "with_identical_lines_same_day": sum("identical_lines_same_day" in s["traits"] for s in statements),
        "unique_transactions": sum(a["unique_transactions"] for a in manifest["accounts"].values()),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    problems = verify(out, manifest, truth)
    t = manifest["totals"]
    print("wrote %d statements (%d partial, %d tail) in %d layouts, %d unique transactions -> %s"
          % (t["statements"], t["partial_exports"], t["tail_exports"], len(t["layouts"]),
             t["unique_transactions"], out))
    if problems:
        print("SELF-CHECK FAILED:\n  " + "\n  ".join(problems[:20]), file=sys.stderr)
        return 1
    print("self-check ok: every file re-reads to the lines and balances recorded in the manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
