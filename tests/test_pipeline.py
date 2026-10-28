"""End-to-end checks: the committed results reproduce, the report has no
unfilled fields, and the optional original-submission slot works."""

import shutil
from pathlib import Path

import pandas as pd
import pytest

from cgpm.data import load_outcome_2026, load_pre_games
from cgpm.pipeline import run
from cgpm.ranking import rank_from_table
from cgpm.report import write_report

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


@pytest.fixture(scope="module")
def fresh(tmp_path_factory):
    out = tmp_path_factory.mktemp("results")
    metrics = run(DATA, out, make_figures=False, make_report=False)
    return out, metrics


def test_committed_results_reproduce(fresh):
    out, _ = fresh
    committed = ROOT / "results/tables"
    if not (committed / "scores.csv").exists():
        pytest.skip("no committed results yet")
    for name in ["scores.csv", "paired_differences.csv", "ranks_by_nation.csv", "historical_carry_forward.csv"]:
        a = pd.read_csv(out / "tables" / name)
        b = pd.read_csv(committed / name)
        pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-12, atol=1e-12)


def test_report_has_no_unfilled_fields(fresh, tmp_path):
    out, metrics = fresh
    path = write_report(tmp_path, metrics, out)
    text = path.read_text()
    body = text.split("## 8. Reproduce")[0]
    assert "{" not in body and "}" not in body
    assert "nan" not in body.lower().replace("financ", "")


def test_original_slot_scores_a_supplied_file(tmp_path):
    """A test-only file equal to the truth must score exactly the ceiling.

    This fixture is built from the 2026 results purely to exercise the code
    path. It is never written to the real data directory.
    """
    shutil.copytree(DATA, tmp_path / "data")
    pre = load_pre_games(tmp_path / "data")
    truth = rank_from_table(load_outcome_2026(tmp_path / "data", pre.nations))
    pd.DataFrame({"Country": truth.index, "Rank": truth.to_numpy()}).to_csv(
        tmp_path / "data/forecast/original_submission.csv", index=False)
    m = run(tmp_path / "data", tmp_path / "results", make_figures=False, make_report=False)
    assert m["original_supplied"]
    assert m["scores"]["original"]["tau"] == pytest.approx(m["tau_ceiling"])
    assert "original - B1" in m["differences"]


def test_readme_numbers_match_results(fresh):
    _, m = fresh
    readme = (ROOT / "README.md").read_text().replace("−", "-")
    s, d = m["scores"], m["differences"]
    expected = [
        f"{m['tau_ceiling']:.3f}",
        f"{s['B1']['tau']:.3f}", f"[{s['B1']['ci95_low']:.3f}, {s['B1']['ci95_high']:.3f}]",
        f"{s['B1p']['tau']:.3f}", f"[{s['B1p']['ci95_low']:.3f}, {s['B1p']['ci95_high']:.3f}]",
        f"{s['B2']['tau']:.3f}", f"[{s['B2']['ci95_low']:.3f}, {s['B2']['ci95_high']:.3f}]",
        f"{d['B1 - B2']['difference']:.3f}", f"[{d['B1 - B2']['ci95_low']:.3f}, {d['B1 - B2']['ci95_high']:.3f}]",
        f"{d['B1p - B1']['difference']:.3f}", f"[{d['B1p - B1']['ci95_low']:.3f}, {d['B1p - B1']['ci95_high']:.3f}]",
        f"{s['B1']['tau_b_reference']:.3f}",
        f"{m['pairs_tied_in_truth']}",
    ]
    missing = [e for e in expected if e not in readme]
    assert not missing, f"README is out of date: {missing}"
