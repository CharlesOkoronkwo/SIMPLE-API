import pytest

from ledger.money import format_naira, parse_amount, round_kobo


def test_plain_number():
    assert parse_amount("250") == 250.0


def test_thousands_separator_and_kobo():
    assert parse_amount("1,250.50") == 1250.50


def test_brackets_mean_negative():
    assert parse_amount("(1,200.50)") == -1200.50


def test_leading_minus_means_negative():
    assert parse_amount("-75.00") == -75.0


def test_naira_sign_and_spaces_are_ignored():
    assert parse_amount("₦ 2,000.00") == 2000.0
    assert parse_amount("NGN 3,000") == 3000.0


def test_large_amount_with_two_separators():
    assert parse_amount("1,250,000.00") == 1250000.0


@pytest.mark.parametrize("text", ["", "   ", "abc", "12.345", "1,2,3x", "()"])
def test_bad_amounts_are_rejected(text):
    with pytest.raises(ValueError):
        parse_amount(text)


def test_none_is_rejected():
    with pytest.raises(ValueError):
        parse_amount(None)


def test_round_kobo():
    assert round_kobo(10.005 + 0.001) == 10.01


def test_format_naira():
    assert format_naira(1234.5) == "₦1,234.50"
    assert format_naira(-99) == "-₦99.00"
