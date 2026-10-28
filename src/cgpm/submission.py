"""Loading and validating the original competition submission, if supplied.

The repository runs without it. If ``data/forecast/original_submission.csv``
exists it is validated against the official rules (74 nations, one numeric
rank each) and scored alongside the baselines, labelled as the original,
pre-registered forecast.

The file must be the one actually emailed before 23:59 BST on 22 July 2026,
unchanged. Name differences with this repository's nation list are handled
by ``data/forecast/name_aliases.csv``; ranks are never edited.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

COUNTRY_COLUMNS = ("Country", "country", "Nation", "nation", "CGA", "Team", "team")


class SubmissionError(ValueError):
    pass


def load_submission(path: Path, nations: pd.DataFrame, aliases_path: Path | None = None) -> pd.Series:
    df = pd.read_csv(path)
    country_col = next((c for c in COUNTRY_COLUMNS if c in df.columns), None)
    rank_col = next((c for c in df.columns if c.strip().lower() == "rank"), None)
    if country_col is None or rank_col is None:
        raise SubmissionError(f"need a country column and a 'Rank' column, found {list(df.columns)}")
    aliases = {}
    if aliases_path is not None and Path(aliases_path).exists():
        a = pd.read_csv(aliases_path)
        aliases = dict(zip(a["submission_name"].str.strip(), a["nation"].str.strip()))
    names = df[country_col].astype(str).str.strip().map(lambda s: aliases.get(s, s))
    ranks = pd.to_numeric(df[rank_col], errors="coerce")
    if ranks.isna().any():
        bad = df.loc[ranks.isna(), country_col].tolist()
        raise SubmissionError(f"non-numeric or missing ranks for {bad}")
    if names.duplicated().any():
        raise SubmissionError(f"duplicated nations: {names[names.duplicated()].tolist()}")
    official = set(nations["nation"])
    unknown = set(names) - official
    missing = official - set(names)
    if unknown or missing:
        raise SubmissionError(
            f"names do not match the 74 CGAs. Unmatched in file: {sorted(unknown)}; "
            f"absent from file: {sorted(missing)}. Add rows to data/forecast/name_aliases.csv."
        )
    return pd.Series(ranks.to_numpy(dtype=float), index=names.to_numpy(), name="rank").loc[nations["nation"]]
