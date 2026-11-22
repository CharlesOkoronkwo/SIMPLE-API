CREATE TABLE IF NOT EXISTS accounts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL UNIQUE,
    layout           TEXT NOT NULL,
    opening_balance  REAL NOT NULL DEFAULT 0,
    currency         TEXT NOT NULL DEFAULT 'NGN',
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id   INTEGER NOT NULL REFERENCES accounts(id),
    posted_on    TEXT NOT NULL,
    description  TEXT NOT NULL,
    amount       REAL NOT NULL,
    reference    TEXT,
    category     TEXT,
    source_file  TEXT,
    imported_at  TEXT,
    UNIQUE (account_id, reference)
);

CREATE INDEX IF NOT EXISTS idx_tx_account_date
    ON transactions (account_id, posted_on);

CREATE TABLE IF NOT EXISTS category_rules (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword   TEXT NOT NULL UNIQUE,
    category  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS budgets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id   INTEGER NOT NULL REFERENCES accounts(id),
    category     TEXT NOT NULL,
    monthly_cap  REAL NOT NULL,
    UNIQUE (account_id, category)
);

CREATE TABLE IF NOT EXISTS imports (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id    INTEGER NOT NULL REFERENCES accounts(id),
    filename      TEXT NOT NULL,
    layout        TEXT NOT NULL,
    rows_read     INTEGER NOT NULL,
    rows_added    INTEGER NOT NULL,
    rows_skipped  INTEGER NOT NULL,
    imported_at   TEXT NOT NULL
);
