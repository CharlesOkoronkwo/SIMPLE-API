"""Readers for the statement layouts we know about.

Each layout takes the rows of a CSV (as dicts) and returns ParsedRow objects
plus a list of problems for lines it could not read.
"""

from ..dates import ISO, parse_date, sniff_date_format
from ..models import ParsedRow
from ..money import parse_amount


class Layout:
    name = ""
    columns = ()

    def matches(self, fieldnames):
        have = {f.strip().lower() for f in fieldnames if f}
        return all(c.lower() in have for c in self.columns)

    def parse(self, rows):
        raise NotImplementedError


def clean(row):
    """Strip header and cell whitespace so lookups are predictable."""
    return {(k or "").strip(): (v or "").strip() for k, v in row.items()}


class BankALayout(Layout):
    """Current account export with separate Debit and Credit columns.

    Date,Description,Debit,Credit,Balance
    05/03/2025,POS PURCHASE SHOPRITE,"12,400.00",,"310,200.50"
    """

    name = "bank_a"
    columns = ("Date", "Description", "Debit", "Credit", "Balance")

    def parse(self, rows):
        rows = [clean(r) for r in rows]
        fmt = sniff_date_format([r["Date"] for r in rows])
        parsed = []
        problems = []
        for number, row in enumerate(rows, start=2):
            if not row["Date"]:
                continue  # blank or footer line
            try:
                posted = parse_date(row["Date"], fmt)
                if row["Debit"]:
                    amount = -abs(parse_amount(row["Debit"]))
                elif row["Credit"]:
                    amount = parse_amount(row["Credit"])
                else:
                    raise ValueError("no debit or credit amount")
                balance = parse_amount(row["Balance"]) if row["Balance"] else None
            except ValueError as err:
                problems.append("line %d: %s" % (number, err))
                continue
            parsed.append(
                ParsedRow(
                    posted_on=posted.strftime(ISO),
                    description=row["Description"],
                    amount=amount,
                    reference=None,
                    balance=balance,
                )
            )
        return parsed, problems


class BankBLayout(Layout):
    """Savings and wallet export with one signed Amount column and a Ref.

    Posted,Narration,Amount,Ref
    2025-03-05,NIP TRANSFER TO ADA,(5000.00),FT25064A1B2C
    """

    name = "bank_b"
    columns = ("Posted", "Narration", "Amount", "Ref")

    def parse(self, rows):
        parsed = []
        problems = []
        for number, row in enumerate((clean(r) for r in rows), start=2):
            if not row["Posted"]:
                continue
            try:
                posted = parse_date(row["Posted"], ISO)
                amount = parse_amount(row["Amount"])
            except ValueError as err:
                problems.append("line %d: %s" % (number, err))
                continue
            parsed.append(
                ParsedRow(
                    posted_on=posted.strftime(ISO),
                    description=row["Narration"],
                    amount=amount,
                    reference=row["Ref"] or None,
                )
            )
        return parsed, problems


LAYOUTS = {
    BankALayout.name: BankALayout(),
    BankBLayout.name: BankBLayout(),
}


def detect_layout(fieldnames):
    for layout in LAYOUTS.values():
        if layout.matches(fieldnames or []):
            return layout
    raise ValueError("this file does not look like a statement we know")


def get_layout(name):
    if name not in LAYOUTS:
        raise ValueError("no importer for layout %r" % name)
    return LAYOUTS[name]
