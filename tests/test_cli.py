from ledger import cli


def run(capsys, *argv):
    code = cli.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_add_account_and_list(capsys):
    assert run(capsys, "add-account", "Main", "--layout", "bank_a", "--opening", "5000")[0] == 0
    code, out, _ = run(capsys, "accounts")
    assert "Main" in out and "5,000.00" in out


def test_import_and_balance(capsys, write_csv):
    run(capsys, "add-account", "Savings", "--layout", "bank_b", "--opening", "10000")
    path = write_csv("b.csv", "Posted,Narration,Amount,Ref\n2025-03-05,NIP TO ADA,(2500.00),FT1\n")
    code, out, _ = run(capsys, "import", "1", str(path))
    assert "added 1" in out
    code, out, _ = run(capsys, "balance", "1", "--as-of", "2025-03-31")
    assert "7,500.00" in out


def test_errors_exit_with_one(capsys):
    code, _, err = run(capsys, "balance", "9")
    assert code == 1
    assert "no account" in err


def test_summary_prints_the_month(capsys):
    run(capsys, "add-account", "Main", "--opening", "1000")
    code, out, _ = run(capsys, "summary", "1", "2025-03")
    assert "summary for 2025-03" in out
