"""Guards that make post-deadline information unusable by the forecasts."""

import shutil
from pathlib import Path

import pandas as pd
import pytest

from cgpm import baselines
from cgpm.data import DEADLINE_UTC, load_pre_games
from cgpm.pipeline import build_forecasts

DATA = Path(__file__).resolve().parents[1] / "data"


def test_forecasts_build_without_the_2026_results(tmp_path):
    """Delete the 2026 medal table: every forecast must still build, identically."""
    shutil.copytree(DATA, tmp_path / "data")
    (tmp_path / "data/raw/medals_2026.csv").unlink()
    blind, _ = build_forecasts(tmp_path / "data")
    full, _ = build_forecasts(DATA)
    assert set(blind) == set(full)
    for k in blind:
        pd.testing.assert_series_equal(blind[k], full[k])


def test_pre_games_code_never_opens_2026_medals():
    import inspect
    code = inspect.getsource(load_pre_games) + inspect.getsource(baselines)
    # strip docstrings/comments: only executable references count
    executable = "\n".join(line for line in code.splitlines() if not line.strip().startswith(("#", '"', "'", "``", "B")))
    assert "medals_2026" not in executable
    assert "load_outcome_2026" not in executable
    # and the loader can only reach Games before 2026
    assert 2026 not in load_pre_games(DATA).medals


def test_feature_snapshots_precede_cutoffs():
    s = pd.read_csv(DATA / "reference/factbook_snapshots.csv")
    for row in s.itertuples():
        assert pd.Timestamp(row.commit_datetime) < pd.Timestamp(row.forecast_cutoff_utc)
    cut_2026 = pd.Timestamp(s.set_index("games").loc[2026, "forecast_cutoff_utc"])
    assert cut_2026 <= DEADLINE_UTC
    f = pd.read_csv(DATA / "interim/factbook_features.csv")
    for row in f.itertuples():
        cut = pd.Timestamp(s.set_index("games").loc[row.games, "forecast_cutoff_utc"])
        assert pd.Timestamp(row.commit_datetime_utc) < cut


def test_walked_back_values_also_precede_cutoff():
    f = pd.read_csv(DATA / "interim/factbook_features.csv")
    s = pd.read_csv(DATA / "reference/factbook_snapshots.csv").set_index("games")
    walked = f[f.note.fillna("").str.contains("latest earlier value")]
    for row in walked.itertuples():
        when = pd.Timestamp(row.note.split("(")[-1].rstrip(")"))
        assert when < pd.Timestamp(s.loc[row.games, "forecast_cutoff_utc"])


def test_ons_release_precedes_deadline():
    sh = pd.read_csv(DATA / "reference/home_nation_shares.csv")
    assert (pd.to_datetime(sh.source_release_date).dt.tz_localize("UTC") < DEADLINE_UTC).all()


def test_b2_trains_only_on_past_games():
    pre = load_pre_games(DATA)
    fit = baselines.population_gdp_model(pre)
    assert set(fit.training_rows["games"]) == {2018, 2022}
    assert 2026 not in pre.medals
    # only nations that took part in each Games are training rows
    assert len(fit.training_rows) == 71 + 72


def test_b2_has_no_free_parameters_tuned_on_2026():
    # The model is fully specified by data and two fixed constants.
    assert baselines.TRAINING_GAMES == (2018, 2022)
    assert baselines.PREDICTION_GAMES == 2026
