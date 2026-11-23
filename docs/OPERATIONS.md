# Operations notes

## All data here is made up

Every statement, name, balance and narration in this repository is invented. Nothing
comes from a real bank, person, employer or client. The sample statements in
`samples/statements/` are invented for testing, and the larger set
produced by `tools/make_statements.py` is generated from a fixed random seed.
Do not add real statements to this repository.

## The database file

There is no committed database. `data/ledger.db` is created on first use and is ignored
by git. To work on a throwaway copy, point `LEDGER_DB` at a scratch file:

```bash
export LEDGER_DB=/tmp/scratch.db
```

Tests already do this: every test gets its own temporary database.

## Backups

Before anything risky on a database you care about, copy the file:
`cp data/ledger.db /tmp/ledger-backup.db`.

## Imports

Bank statements arrive as CSV files. People sometimes import a part-month export and
then the full month later, so the same lines can appear in two files. Importing the same
file twice, or two overlapping files, must not create duplicate transactions. This is
a known gap in the starter code and is tracked under "Known issues" in the README.

## Deploying

Ledger is a local tool and is not deployed anywhere. The earlier Terraform, Docker and
workflow files from the original SIMPLE-API experiment live in `legacy-deploy/` and are
not used.
