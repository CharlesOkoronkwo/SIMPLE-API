import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DB = ROOT / "data" / "ledger.db"

# Layout names an account can use. "manual" accounts have no importer.
LAYOUTS = ("bank_a", "bank_b", "manual")

CURRENCY = "NGN"


def db_path():
    """Where the database lives. Set LEDGER_DB to point somewhere else."""
    return os.environ.get("LEDGER_DB", str(DEFAULT_DB))
