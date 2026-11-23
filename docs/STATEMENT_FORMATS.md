# Statement formats

The importer reads CSV files exported from the bank's web banking. The layout
is chosen by the account (`bank_a`, `bank_b`) or detected from the header row
for `manual` accounts.

## bank_a (current accounts)

```
Date,Description,Debit,Credit,Balance
,Opening Balance,,,"285,400.50"
02/01/2025,TRANSFER TO LANDLORD RENT,"90,000.00",,"195,400.50"
25/01/2025,SALARY PAYMENT ACME LOGISTICS,,"450,000.00","645,400.50"
,Closing Balance,,,"645,400.50"
```

- Dates are day/month/year.
- Debits and credits sit in separate columns. Amounts use commas for thousands.
- The Balance column is the bank's running balance after each line.
- The first and last lines have no date. They carry the opening and closing balance.
- A reversal of an earlier debit is printed in brackets in the Debit column,
  for example `(2,500.00)`. It means the money came BACK: the running balance goes up
  by that amount, so it is stored as a positive (credit) amount. (The starter importer
  gets this wrong; see "Known issues" in the README.)
- There is no reference column.

## bank_b (savings and wallet accounts)

```
Posted,Narration,Amount,Ref
2025-03-05,NIP TRANSFER TO ADA,(5000.00),FT250305B0003
2025-03-31,INTEREST,311.42,FT250331B0013
,Closing balance,"95,610.68",
```

- Dates are `YYYY-MM-DD`.
- One signed Amount column. Money out is in brackets. Some amounts have
  thousands commas and some do not.
- Every line has a bank reference.
- The last line has no date and carries the closing balance.

## bank_c and bank_d (specified, not yet importable)

These two layouts are produced by `tools/make_statements.py` so the importer work has
something to aim at. Both are invented.

```
Value Date,Narrative,Amount (NGN),Balance (NGN)
,BALANCE B/F,,"285,400.50"
01-Feb-2024,TRANSFER TO LANDLORD RENT,"-90,000.00","195,400.50"
,BALANCE C/F,,"195,400.50"
```

bank_c: dates are `dd-Mon-yyyy`; one signed Amount with a minus sign for money out; a
running Balance on every line; opening and closing lines carry no date.

```
Date;Ref;Narration;Dr/Cr;Amount;Balance
;;Opening balance;;;₦285,400.50
01.02.2024;D240201-0052;BOLT TRIP;DR;₦4,701.64;₦280,698.86
;;Closing balance;;;₦280,698.86
```

bank_d: semicolon separated; dates are `dd.mm.yyyy`; the direction is in a `Dr/Cr` column
and the amount is unsigned; amounts carry a naira sign; every line has a reference;
files start with a byte order mark and use CRLF line endings.

## Part-month exports

A statement can cover only part of a month: from the 1st to a chosen day (an early
export) or from a chosen day to the end (a late one). Their lines are identical to the
same lines in the full-month file, including the running balance, so importing both
must not duplicate anything. Two genuine lines can also be identical on the same day
(same narration and amount); a repeat-safe import must keep both.

## Adding a layout

1. Add a class to `ledger/importer/layouts.py` with `columns` and `parse()`.
2. Register it in `LAYOUTS` and in `ledger/config.py`.
3. Add tests in `tests/test_importer.py`.
