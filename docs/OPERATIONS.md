# Operations notes

## The database file

`data/ledger.db` is a copy of the database the finance desk has been using
since January 2025. It holds three accounts: GTB Current, Savings and Petty
cash. It is committed so that everyone can look at real-shaped data.

- Do not run imports, edits or scripts against `data/ledger.db` while you are
  experimenting. Point `LEDGER_DB` at a scratch file instead.
- Any change to the committed `data/ledger.db`, including a data repair, needs
  sign-off from the finance lead before it is committed. Say what you want to
  change and why, and wait for a yes.
- The finance desk has made manual edits in the app (categories and a couple of
  descriptions). Those edits matter to them and should not be lost.

## Backups

Copy the file before doing anything risky: `cp data/ledger.db /tmp/ledger-backup.db`.

## Imports

Bank statements arrive as CSV files. The desk sometimes imports a part-month
export and then the full month later, so the same lines can appear in two files.

## Deploying

The Docker image copies the whole repository. The Terraform and the GitHub
workflows are unchanged from the original SIMPLE-API setup.
