import pytest

from ledger import db


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    """Every test gets its own database file. Nothing touches data/ledger.db."""
    monkeypatch.setenv("LEDGER_DB", str(tmp_path / "test.db"))


@pytest.fixture
def conn():
    connection = db.connect()
    yield connection
    connection.close()


@pytest.fixture
def write_csv(tmp_path):
    def _write(name, text):
        path = tmp_path / name
        path.write_text(text.lstrip("\n"), encoding="utf-8")
        return path

    return _write
