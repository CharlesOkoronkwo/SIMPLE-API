# Ledger

Ledger is a Flask + SQLite service and command line tool for Naira bank accounts. Today
it imports CSV statements in two bank layouts, keeps transactions and balances, and gives
monthly summaries and budgets. The aim is to grow it into an engine that reconciles
statements to the kobo (see Goal).

## Provenance

This repository began as SIMPLE-API, a tiny Flask `/time` endpoint with deployment
experiments (now in `legacy-deploy/`, unused). The Ledger code, its 99 tests and the sample
statements were drafted with AI assistance for an earlier task. I am the owner of the
repository and responsible for it; I have not independently audited the starter code,
and it contains known bugs (below). All data in the repository is made up.

## Goal

Statements from at least four layouts import so that every closing balance matches the
bank's exactly; re-importing a file, or importing an overlapping file, never adds
duplicates; money is stored as integer kobo, not floats; and summarising 100,000
transactions takes under 200 ms.

## Known issues in the starter code

These are real defects, pinned by `xfail(strict=True)` tests in `tests/test_known_issues.py`
so they cannot be forgotten and cannot pass silently when fixed:

1. **Bracketed debit reversals get the wrong sign.** `(2,500.00)` in the Debit column means
   money came back, but the importer stores it as a debit.
2. **Dates can be read day/month swapped.** When the first rows of a `bank_a` file all have a
   day of 12 or less, `01/02/2025` is read as 2 January instead of 1 February.
3. **Overlapping `bank_a` imports duplicate rows.** `bank_a` has no reference column, so the
   `UNIQUE (account_id, reference)` rule never fires on `NULL`.

With the samples in `samples/statements/` these three together turn a correct 31 March
balance of 721,128.19 into 875,576.72.

Other things the starter does not do yet: money is `REAL` (float), only two layouts are
supported, and nothing reconciles against the bank's running balances.

A small Flask + SQLite service for tracking Naira bank accounts. It keeps the
original `/time` endpoint and adds accounts, transactions, bank statement
imports, monthly summaries and simple budgets.

## Layout

```
app.py                Flask app (/time and the /api routes)
ledger/
  db.py, schema.sql   SQLite connection and tables
  money.py, dates.py  parsing helpers for bank text
  accounts.py         accounts
  transactions.py     transactions and balances
  categories.py       keyword rules that label transactions
  summary.py          monthly numbers for the dashboard
  budgets.py          monthly caps per category
  export.py           CSV export
  importer/           bank statement layouts and the import step
  api.py              HTTP routes
  cli.py              command line tool
samples/statements/   example bank statements
legacy-deploy/        earlier deployment experiment (unused)
tools/                statement generator and checker
tests/                pytest tests
docs/                 notes on formats and operations
```

## Running it

```bash
pip install -r requirements.txt -r requirements-dev.txt
python app.py                 # serves on port 8080
python -m pytest              # runs the tests
```

The database file is `data/ledger.db`. Set `LEDGER_DB` to use a different one:

```bash
export LEDGER_DB=/tmp/scratch.db
```

## Command line

```bash
python -m ledger.cli add-account "GTB Current" --layout bank_a --opening 285400.50
python -m ledger.cli import 1 samples/statements/gtb-2025-01.csv
python -m ledger.cli balance 1 --as-of 2025-01-31
python -m ledger.cli summary 1 2025-01
python -m ledger.cli transactions 1 --category groceries
```

## HTTP routes

| Route | What it does |
| --- | --- |
| `GET /api/health` | quick check |
| `GET, POST /api/accounts` | list or create accounts |
| `GET, PATCH, DELETE /api/accounts/<id>` | one account |
| `GET /api/accounts/<id>/balance?as_of=2025-03-31` | balance on a date |
| `GET, POST /api/accounts/<id>/transactions` | list (filters: start, end, category, q) or add |
| `PATCH, DELETE /api/transactions/<id>` | edit or remove one |
| `POST /api/accounts/<id>/import` | upload a bank statement CSV (field `file`) |
| `GET /api/accounts/<id>/imports` | import history |
| `GET /api/accounts/<id>/summary?month=2025-03` | monthly numbers |
| `GET /api/accounts/<id>/series`, `/compare`, `/running-balance` | chart data |
| `GET /api/accounts/<id>/export.csv` | download transactions |
| `GET, PUT /api/accounts/<id>/budgets` | budgets and how much is used |
| `GET, POST /api/rules` | category rules |

Amounts are in Naira. Money going out is negative.

## Statement formats

See `docs/STATEMENT_FORMATS.md`. Two layouts are supported today: `bank_a`
(Debit and Credit columns) and `bank_b` (one signed Amount column with a Ref).
`bank_c` and `bank_d` are specified there and produced by the generator, but not yet
importable.

## Working on the database

There is no committed database: `data/ledger.db` is created on first use and is git-ignored.
See `docs/OPERATIONS.md`.

## Large made-up test set

```bash
python tools/make_statements.py          # writes samples/generated/ (git-ignored)
python tools/check_statements.py         # imports it all and compares to manifest.json
```

The generator is deterministic (fixed seed) and writes 200+ statements in four layouts
with the expected closing balance of every statement in `samples/generated/manifest.json`.
