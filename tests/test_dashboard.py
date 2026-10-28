"""The dashboard embeds results by code: its numbers must equal metrics.json,
and the page must load nothing from the network."""

import json
import re
from pathlib import Path

import pytest

from cgpm.dashboard import write_dashboard
from cgpm.pipeline import run

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("dash")
    m = run(DATA, tmp / "results", make_figures=False, make_report=False, make_dashboard=False)
    path = write_dashboard(tmp, m, tmp / "results")
    html = path.read_text()
    payload = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S)
                         .group(1).replace("<\\/", "</"))
    return html, payload, m


def test_numbers_match_metrics(page):
    _, p, m = page
    assert p["ceiling"] == pytest.approx(m["tau_ceiling"])
    for s in p["scores"]:
        ref = m["scores"][s["id"]]
        assert s["tau"] == pytest.approx(ref["tau"])
        assert (s["lo"], s["hi"]) == (pytest.approx(ref["ci95_low"]), pytest.approx(ref["ci95_high"]))
    assert len(p["nations"]) == 74
    for n in p["nations"]:
        r = m["ranks"][n["nation"]]
        assert n["true"] == r["true_rank"] and n["B1"] == r["B1_rank"] and n["B2"] == r["B2_rank"]
        assert n["B1_c"] + n["B1_d"] <= 73


def test_no_network_dependencies(page):
    html, _, _ = page
    assert not re.search(r'<(script|link|img)[^>]+(src|href)="https?://', html)


def test_no_references_to_a_competition_entry(page):
    html, _, _ = page
    assert "original" not in html.lower()
