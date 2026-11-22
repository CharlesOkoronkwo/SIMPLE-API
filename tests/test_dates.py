import pytest

from ledger import dates


def test_iso_dates_are_recognised():
    assert dates.sniff_date_format(["2025-03-05", "2025-03-06"]) == dates.ISO


def test_day_first_when_first_part_is_over_12():
    assert dates.sniff_date_format(["15/03/2025", "16/03/2025"]) == dates.DAY_FIRST


def test_month_first_when_second_part_is_over_12():
    assert dates.sniff_date_format(["03/15/2025"]) == dates.MONTH_FIRST


def test_parse_date_uses_the_given_format():
    assert dates.parse_date("15/03/2025", dates.DAY_FIRST).isoformat() == "2025-03-15"


def test_parse_date_falls_back_to_another_format():
    assert dates.parse_date("2025-03-15", dates.DAY_FIRST).isoformat() == "2025-03-15"


def test_parse_date_rejects_nonsense():
    with pytest.raises(ValueError):
        dates.parse_date("31/31/2025", dates.DAY_FIRST)


def test_month_bounds():
    assert dates.month_bounds("2025-03") == ("2025-03-01", "2025-03-31")
    assert dates.month_bounds("2024-02") == ("2024-02-01", "2024-02-29")
    assert dates.month_bounds("2025-02") == ("2025-02-01", "2025-02-28")


@pytest.mark.parametrize("text", ["2025-13", "2025-3", "March", ""])
def test_bad_months_are_rejected(text):
    with pytest.raises(ValueError):
        dates.parse_month(text)


def test_previous_month_wraps_the_year():
    assert dates.previous_month("2025-01") == "2024-12"
    assert dates.previous_month("2025-03") == "2025-02"


def test_last_months_is_oldest_first():
    assert dates.last_months("2025-02", 3) == ["2024-12", "2025-01", "2025-02"]


def test_day_before():
    assert dates.day_before("2025-03-01") == "2025-02-28"
