"""Known defects in the starter importer, pinned as strict expected failures.

Each test describes the CORRECT behaviour. While the bug exists the test fails, which
pytest reports as xfail. When the bug is fixed the test passes, strict mode turns that
into a failure, and whoever fixed it removes the marker. See "Known issues" in the README.
"""

from pathlib import Path

import pytest

from ledger import accounts, transactions
from ledger.importer import import_file

SAMPLES = Path(__file__).resolve().parent.parent / "samples" / "statements"


@pytest.fixture
def current(conn):
    return accounts.create_account(conn, "Current", "bank_a", 100000)


@pytest.mark.xfail(strict=True, reason="issue 1: bracketed debit reversal stored as a debit")
def test_bracketed_debit_reversal_gives_money_back(conn, current, write_csv):
    # The bank's running balance goes UP by 250.00, so this line is a credit.
    text = """
Date,Description,Debit,Credit,Balance
,Opening Balance,,,"100,000.00"
20/03/2025,REVERSAL POS PURCHASE,(250.00),,"100,250.00"
,Closing Balance,,,"100,250.00"
"""
    import_file(conn, current.id, write_csv("a.csv", text))
    assert transactions.list_transactions(conn, current.id)[0].amount == 250.0
    assert transactions.balance_as_of(conn, current.id, "2025-03-31") == 100250.0


@pytest.mark.xfail(strict=True, reason="issue 2: ambiguous dd/mm dates read month-first")
def test_day_first_dates_are_not_swapped(conn, current, write_csv):
    # The importer only looks at the first five dated rows to pick a format. Here every
    # day in those rows is 12 or less, and only the sixth (20/02) shows it is day-first.
    text = """
Date,Description,Debit,Credit,Balance
,Opening Balance,,,"100,000.00"
01/02/2025,POS PURCHASE SPAR,"1,000.00",,"99,000.00"
02/02/2025,POS PURCHASE SPAR,"1,000.00",,"98,000.00"
03/02/2025,POS PURCHASE SPAR,"1,000.00",,"97,000.00"
04/02/2025,POS PURCHASE SPAR,"1,000.00",,"96,000.00"
05/02/2025,POS PURCHASE SPAR,"1,000.00",,"95,000.00"
20/02/2025,POS PURCHASE SPAR,"1,000.00",,"94,000.00"
,Closing Balance,,,"94,000.00"
"""
    import_file(conn, current.id, write_csv("a.csv", text))
    dates = [t.posted_on for t in transactions.list_transactions(conn, current.id)]
    assert dates == ["2025-02-01", "2025-02-02", "2025-02-03",
                     "2025-02-04", "2025-02-05", "2025-02-20"]


@pytest.mark.xfail(strict=True, reason="issue 3: bank_a has no reference, overlaps duplicate")
def test_overlapping_bank_a_imports_add_no_duplicates(conn, current, write_csv):
    part = """
Date,Description,Debit,Credit,Balance
,Opening Balance,,,"100,000.00"
15/03/2025,POS PURCHASE SHOPRITE,"12,400.00",,"87,600.00"
16/03/2025,SALARY PAYMENT ACME,,"450,000.00","537,600.00"
,Closing Balance,,,"537,600.00"
"""
    full = """
Date,Description,Debit,Credit,Balance
,Opening Balance,,,"100,000.00"
15/03/2025,POS PURCHASE SHOPRITE,"12,400.00",,"87,600.00"
16/03/2025,SALARY PAYMENT ACME,,"450,000.00","537,600.00"
20/03/2025,MTN AIRTIME,"1,000.00",,"536,600.00"
,Closing Balance,,,"536,600.00"
"""
    import_file(conn, current.id, write_csv("part.csv", part))
    import_file(conn, current.id, write_csv("full.csv", full))
    assert transactions.count_transactions(conn, current.id) == 3
    assert transactions.balance_as_of(conn, current.id, "2025-03-31") == 536600.0


@pytest.mark.xfail(strict=True, reason="issues 1-3 together: sample balances are wrong")
def test_sample_statements_reproduce_the_known_balances(conn):
    acct = accounts.create_account(conn, "GTB Current", "bank_a", 285400.50)
    for name in ["gtb-2025-01.csv", "gtb-2025-02.csv",
                 "gtb-2025-03-to-8th.csv", "gtb-2025-03.csv"]:
        import_file(conn, acct.id, SAMPLES / name)
    assert transactions.balance_as_of(conn, acct.id, "2025-01-31") == 551917.02
    assert transactions.balance_as_of(conn, acct.id, "2025-02-28") == 735610.12
    assert transactions.balance_as_of(conn, acct.id, "2025-03-31") == 721128.19
    assert transactions.count_transactions(conn, acct.id, "2025-03-01", "2025-03-31") == 75

    savings = accounts.create_account(conn, "Savings", "bank_b", 50000)
    import_file(conn, savings.id, SAMPLES / "savings-2025-03.csv")
    assert transactions.balance_as_of(conn, savings.id, "2025-03-31") == 95610.68
