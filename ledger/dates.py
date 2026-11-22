import calendar
import re
from datetime import date, datetime, timedelta

ISO = "%Y-%m-%d"
DAY_FIRST = "%d/%m/%Y"
MONTH_FIRST = "%m/%d/%Y"

# Formats we try, in order, when the main guess does not fit a value.
FALLBACKS = (DAY_FIRST, MONTH_FIRST, ISO, "%d-%b-%Y")

ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
MONTH_RE = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


def sniff_date_format(values):
    """Guess the date format of a statement from its first few rows."""
    head = [v.strip() for v in values[:5] if v and v.strip()]
    for text in head:
        if ISO_RE.fullmatch(text):
            return ISO
    for text in head:
        parts = text.split("/")
        if len(parts) != 3:
            continue
        if int(parts[0]) > 12:
            return DAY_FIRST
        if int(parts[1]) > 12:
            return MONTH_FIRST
    return MONTH_FIRST


def parse_date(text, fmt):
    """Read one date, trying the guessed format first."""
    text = text.strip()
    order = [fmt] + [f for f in FALLBACKS if f != fmt]
    for candidate in order:
        try:
            return datetime.strptime(text, candidate).date()
        except ValueError:
            continue
    raise ValueError("unreadable date: %r" % text)


def parse_iso(text):
    return datetime.strptime(text, ISO).date()


def parse_month(text):
    """'2025-03' -> (2025, 3). Raises ValueError for anything else."""
    if not MONTH_RE.fullmatch(text or ""):
        raise ValueError("month must look like 2025-03")
    return int(text[:4]), int(text[5:7])


def month_bounds(month):
    """First and last day of a 'YYYY-MM' month, as ISO text."""
    year, mon = parse_month(month)
    last = calendar.monthrange(year, mon)[1]
    return "%04d-%02d-01" % (year, mon), "%04d-%02d-%02d" % (year, mon, last)


def previous_month(month):
    year, mon = parse_month(month)
    if mon == 1:
        return "%04d-12" % (year - 1)
    return "%04d-%02d" % (year, mon - 1)


def last_months(month, count):
    """The given month and the ones before it, oldest first."""
    months = [month]
    while len(months) < count:
        months.append(previous_month(months[-1]))
    months.reverse()
    return months


def day_before(iso_text):
    return (parse_iso(iso_text) - timedelta(days=1)).strftime(ISO)


def today_iso():
    return date.today().strftime(ISO)
