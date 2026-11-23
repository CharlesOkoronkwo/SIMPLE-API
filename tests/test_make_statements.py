"""The statement generator is the oracle for the importer work, so it gets its own tests."""

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "make_statements.py"


def load():
    spec = importlib.util.spec_from_file_location("make_statements", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_small_set_is_self_consistent_and_has_all_layouts(tmp_path):
    gen = load()
    assert gen.main(["--out", str(tmp_path), "--accounts", "4", "--months", "4"]) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["totals"]["layouts"] == ["bank_a", "bank_b", "bank_c", "bank_d"]
    assert manifest["totals"]["statements"] >= 16
    for acct in manifest["accounts"].values():
        fulls = [s for s in acct["statements"] if s["kind"] == "full"]
        for earlier, later in zip(fulls, fulls[1:]):
            assert earlier["closing_kobo"] == later["opening_kobo"]


def test_same_seed_gives_identical_files(tmp_path):
    gen = load()
    one, two = tmp_path / "one", tmp_path / "two"
    gen.main(["--out", str(one), "--accounts", "4", "--months", "3"])
    gen.main(["--out", str(two), "--accounts", "4", "--months", "3"])
    names = sorted(p.relative_to(one) for p in one.rglob("*") if p.is_file())
    assert names == sorted(p.relative_to(two) for p in two.rglob("*") if p.is_file())
    for name in names:
        assert (one / name).read_bytes() == (two / name).read_bytes()


def test_default_set_meets_the_acceptance_size(tmp_path):
    gen = load()
    assert gen.main(["--out", str(tmp_path)]) == 0
    totals = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["totals"]
    assert totals["statements"] >= 200
    assert len(totals["layouts"]) >= 4
