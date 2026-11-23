#!/usr/bin/env python3
"""Print what this machine has for running Ledger: Python, Flask, pytz, pytest, SQLite."""
import importlib
from importlib import metadata
import sqlite3
import sys

print("python  ", sys.version.split()[0])
print("sqlite  ", sqlite3.sqlite_version)
missing = []
for name in ("flask", "pytz", "pytest"):
    try:
        importlib.import_module(name)
        print("%-8s %s" % (name, metadata.version(name)))
    except ImportError:
        print("%-8s MISSING" % name)
        missing.append(name)
sys.exit(1 if missing else 0)
