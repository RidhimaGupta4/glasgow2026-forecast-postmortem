"""Loading and validating every input file.

Two entry points keep the 2026 results physically separate from everything
used to build a forecast:

* ``load_pre_games`` returns only information that existed before the
  Glasgow 2026 forecast deadline (23:59 BST, 22 July 2026). It never opens
  ``medals_2026.csv``.
* ``load_outcome_2026`` opens the 2026 medal table and is called only by the
  scoring stage.

Every baseline is built from a ``PreGamesData`` object, so a baseline cannot
read the 2026 results even by accident. ``tests/test_leakage_guards.py``
checks this by deleting the 2026 file and building all baselines.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DEADLINE_UTC = pd.Timestamp("2026-07-22T22:59:59Z")  # 23:59 BST
MEDAL_COLS = ["gold", "silver", "bronze"]


@dataclass(frozen=True)
class PreGamesData:
    nations: pd.DataFrame          # the 74 CGAs entered for Glasgow 2026
    medals: dict[int, pd.DataFrame]  # 2014, 2018, 2022 medal tables
    medals_2022_by_sport: pd.DataFrame
    programme_2026: pd.DataFrame
    features: pd.DataFrame         # point-in-time population and GDP
    snapshots: pd.DataFrame


def _read_medals(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected = ["nation", *MEDAL_COLS]
    if list(df.columns) != expected:
        raise ValueError(f"{path.name}: columns {list(df.columns)} != {expected}")
    if df["nation"].duplicated().any():
        raise ValueError(f"{path.name}: duplicated nations")
    if (df[MEDAL_COLS] < 0).any().any():
        raise ValueError(f"{path.name}: negative medal counts")
    return df


def load_pre_games(data_dir: Path) -> PreGamesData:
    data_dir = Path(data_dir)
    nations = pd.read_csv(data_dir / "reference/nations.csv")
    if len(nations) != 74 or nations["nation"].duplicated().any():
        raise ValueError("nations.csv must list the 74 CGAs exactly once")
    medals = {y: _read_medals(data_dir / f"raw/medals_{y}.csv") for y in (2014, 2018, 2022)}
    for y, df in medals.items():
        unknown = set(df["nation"]) - set(nations["nation"])
        if unknown:
            raise ValueError(f"medals_{y}.csv has nations outside the 74-CGA list: {unknown}")
    by_sport = pd.read_csv(data_dir / "raw/medals_2022_by_sport.csv")
    programme = pd.read_csv(data_dir / "reference/programme_2026.csv")
    features = pd.read_csv(data_dir / "interim/factbook_features.csv")
    snapshots = pd.read_csv(data_dir / "reference/factbook_snapshots.csv")
    return PreGamesData(nations, medals, by_sport, programme, features, snapshots)


def load_outcome_2026(data_dir: Path, nations: pd.DataFrame) -> pd.DataFrame:
    """The Glasgow 2026 final medal table for all 74 CGAs (zeros filled in)."""
    df = _read_medals(Path(data_dir) / "raw/medals_2026.csv")
    unknown = set(df["nation"]) - set(nations["nation"])
    if unknown:
        raise ValueError(f"medals_2026.csv has nations outside the 74-CGA list: {unknown}")
    return complete_table(df, nations)


def complete_table(medals: pd.DataFrame, nations: pd.DataFrame) -> pd.DataFrame:
    """Medal table indexed by all 74 nations, with zeros for non-medallists."""
    out = nations[["nation"]].merge(medals, on="nation", how="left").fillna(0)
    out[MEDAL_COLS] = out[MEDAL_COLS].astype(int)
    return out.set_index("nation")
