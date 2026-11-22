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
  for example `(2,500.00)`.
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

## Adding a layout

1. Add a class to `ledger/importer/layouts.py` with `columns` and `parse()`.
2. Register it in `LAYOUTS` and in `ledger/config.py`.
3. Add tests in `tests/test_importer.py`.
