import re

AMOUNT_RE = re.compile(r"\d+(\.\d{1,2})?")


def parse_amount(text):
    """Turn bank text such as '1,250.50' or '(1,200.50)' into a float.

    Brackets and a leading minus both mean a negative number.
    """
    if text is None:
        raise ValueError("missing amount")
    s = text.strip()
    s = s.replace("₦", "").replace("NGN", "").replace(" ", "").replace(" ", "")
    if not s:
        raise ValueError("empty amount")

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    if s.startswith("-"):
        negative = True
        s = s[1:]

    s = s.replace(",", "")
    if not AMOUNT_RE.fullmatch(s):
        raise ValueError("not an amount: %r" % text)

    value = float(s)
    if negative:
        return -value
    return value


def round_kobo(value):
    """Round to two decimal places. Used before showing or comparing totals."""
    return round(value + 0.0, 2)


def format_naira(value):
    value = round_kobo(value)
    sign = "-" if value < 0 else ""
    return "%s₦%s" % (sign, format(abs(value), ",.2f"))
