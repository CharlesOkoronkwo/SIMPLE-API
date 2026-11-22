# Simple API on GCP with GKE

## Description

This repository contains the Terraform code to deploy a simple API to Google Kubernetes Engine (GKE) on Google Cloud Platform (GCP) using Infrastructure as Code (IaC).

## Prerequisites

- Google Cloud SDK
- Terraform
- Docker
- GitHub Actions

## Setup and Deployment

1. Clone the repository.
2. Configure your GCP project and credentials.
3. Run Terraform to deploy the infrastructure:
   ```bash
   terraform init
   terraform apply

---

# Ledger API

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
data/ledger.db        copy of the finance desk database (see docs/OPERATIONS.md)
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

## Working on the database

`data/ledger.db` is a copy of a real working database. Read `docs/OPERATIONS.md`
before changing it.
