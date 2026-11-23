# Sample statements

All data in these files is made up. They imitate the shape of Nigerian web-banking CSV
exports for testing; they are not real statements and do not describe real people.

| File | Account | Covers |
| --- | --- | --- |
| `gtb-2025-01.csv` | Current (bank_a) | January 2025 |
| `gtb-2025-02.csv` | Current (bank_a) | February 2025 |
| `gtb-2025-03-to-8th.csv` | Current (bank_a) | 1 to 8 March 2025, exported early |
| `gtb-2025-03.csv` | Current (bank_a) | all of March 2025 |
| `savings-2025-03.csv` | Savings (bank_b) | March 2025 |

The first and last lines of each file hold the opening and closing balance.

## Known correct figures

Opening balance of the current account on 1 January 2025 is 285,400.50.

| Date | Current account balance |
| --- | --- |
| 31 Jan 2025 | 551,917.02 |
| 28 Feb 2025 | 735,610.12 |
| 31 Mar 2025 | 721,128.19 |

March, current account: money in 486,859.40, money out 501,341.33, 75 transactions.
Savings account closing balance, 31 Mar 2025: 95,610.68.

The part-month file `gtb-2025-03-to-8th.csv` deliberately overlaps with the full March
file. It exists to test duplicate handling.

## Larger generated set

`python tools/make_statements.py` writes 200+ more made-up statements in four layouts
to `samples/generated/` (git-ignored), with a `manifest.json` of expected balances.
See the README.
