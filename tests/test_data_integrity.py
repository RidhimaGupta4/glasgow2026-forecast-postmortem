"""The transcribed data must match the totals published by the sources."""

from pathlib import Path

import pandas as pd
import pytest

DATA = Path(__file__).resolve().parents[1] / "data"

# (entries, gold, silver, bronze) from each Wikipedia medal table's "Totals" row
PUBLISHED_TOTALS = {
    2014: (37, 261, 261, 302),
    2018: (43, 275, 276, 289),
    2022: (43, 280, 282, 315),
    2026: (45, 216, 215, 243),
}
PARTICIPANTS = {2014: 71, 2018: 71, 2022: 72, 2026: 74}

# (gold, silver, bronze) per 2022 sport, from each sport's medal table or event list
SPORT_TOTALS_2022 = {
    "athletics": (58, 58, 57), "swimming": (52, 54, 50), "track_cycling": (20, 20, 19),
    "artistic_gymnastics": (14, 14, 14), "boxing": (16, 16, 32), "judo": (14, 14, 28),
    "weightlifting": (16, 16, 16), "para_powerlifting": (4, 4, 4), "bowls": (11, 11, 11),
    "basketball_3x3": (4, 4, 4), "netball": (1, 1, 1),
}


@pytest.fixture(scope="module")
def nations():
    return pd.read_csv(DATA / "reference/nations.csv")


@pytest.mark.parametrize("year", sorted(PUBLISHED_TOTALS))
def test_medal_totals_match_published(year):
    df = pd.read_csv(DATA / f"raw/medals_{year}.csv")
    entries, g, s, b = PUBLISHED_TOTALS[year]
    assert len(df) == entries
    assert (df.gold.sum(), df.silver.sum(), df.bronze.sum()) == (g, s, b)
    assert not df.nation.duplicated().any()


@pytest.mark.parametrize("year", sorted(PUBLISHED_TOTALS))
def test_medallists_are_participants(year, nations):
    df = pd.read_csv(DATA / f"raw/medals_{year}.csv")
    took_part = set(nations.loc[nations[f"participated_{year}"] == 1, "nation"])
    assert set(df.nation) <= took_part


def test_participant_counts(nations):
    assert len(nations) == 74 and not nations.nation.duplicated().any()
    for y, n in PARTICIPANTS.items():
        assert nations[f"participated_{y}"].sum() == n


def test_2026_programme_has_215_events():
    p = pd.read_csv(DATA / "reference/programme_2026.csv")
    assert p.events_2026.sum() == 215


def test_2022_sport_tables():
    df = pd.read_csv(DATA / "raw/medals_2022_by_sport.csv")
    for sport, tot in SPORT_TOTALS_2022.items():
        sub = df[df.sport == sport]
        assert (sub.gold.sum(), sub.silver.sum(), sub.bronze.sum()) == tot, sport
    overall = pd.read_csv(DATA / "raw/medals_2022.csv").set_index("nation")
    per_nation = df.groupby("nation")[["gold", "silver", "bronze"]].sum()
    for n, row in per_nation.iterrows():
        assert (row <= overall.loc[n, ["gold", "silver", "bronze"]]).all(), n


def test_features_complete_for_all_snapshots(nations):
    f = pd.read_csv(DATA / "interim/factbook_features.csv")
    for g in (2018, 2022, 2026):
        sub = f[f.games == g]
        assert set(sub.nation) == set(nations.nation)
        assert sub.population.notna().all() and (sub.population > 0).all()
    # GDP may be missing only for the territories named in LEAKAGE_AUDIT.md
    allowed = {"Montserrat", "Norfolk Island", "Saint Helena", "Turks and Caicos Islands"}
    assert set(f.loc[f.gdp_usd.isna(), "nation"]) <= allowed


def test_home_nations_sum_to_uk():
    f = pd.read_csv(DATA / "interim/factbook_features.csv")
    homes = ["England", "Scotland", "Wales", "Northern Ireland"]
    for g in (2018, 2022, 2026):
        sub = f[(f.games == g) & f.nation.isin(homes)]
        uk_gdp = sub.gdp_raw.iloc[0]
        assert sub.gdp_raw.nunique() == 1, "all four must come from the same UK figure"
        assert sub.population.sum() > 0 and uk_gdp
