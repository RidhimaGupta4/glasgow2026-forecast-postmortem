"""Naive baselines for the Glasgow 2026 medal table.

Every function here takes a ``PreGamesData`` object and nothing else, so it
can only see information that existed before the forecast deadline.

B0  Default entry: all 74 nations tied. Scores exactly 0 by construction;
    included because it is the competition's own reference point.
B1  Birmingham 2022 carried forward: rank 2026 nations by their 2022 table
    position (gold, silver, bronze). Nations with no 2022 medal tie last.
B1p B1 restricted to the 2026 programme: 2022 medals counted only in sports
    that are on the Glasgow 2026 programme. The programme was public long
    before the deadline. Specified as a decomposition device, see
    ANALYSIS_PLAN.md.
B2  Population and GDP: Poisson regression of gold medals on log population
    and log GDP, with a fixed effect per Games, fitted on 2018 and 2022 only.
    2026 is predicted from the latest Factbook snapshot before the deadline.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .data import DEADLINE_UTC, PreGamesData, complete_table
from .ranking import rank_from_score, rank_from_table

TRAINING_GAMES = (2018, 2022)
PREDICTION_GAMES = 2026


def default_entry(pre: PreGamesData) -> pd.Series:
    return pd.Series(74.0, index=pre.nations["nation"], name="rank")


def carry_forward_2022(pre: PreGamesData) -> pd.Series:
    table = complete_table(pre.medals[2022], pre.nations)
    return rank_from_table(table)


def programme_filtered_2022(pre: PreGamesData) -> tuple[pd.Series, pd.DataFrame]:
    kept = set(pre.programme_2026.loc[pre.programme_2026["on_2022_programme"] == 1, "sport_key"])
    unknown = kept - set(pre.medals_2022_by_sport["sport"])
    if unknown:
        raise ValueError(f"no 2022 per-sport data for {unknown}")
    sub = pre.medals_2022_by_sport[pre.medals_2022_by_sport["sport"].isin(kept)]
    agg = sub.groupby("nation", as_index=False)[["gold", "silver", "bronze"]].sum()
    table = complete_table(agg, pre.nations)
    return rank_from_table(table), table


@dataclass(frozen=True)
class PopGdpFit:
    ranks: pd.Series
    score: pd.Series          # linear predictor without the Games effect
    coefficients: pd.DataFrame
    training_rows: pd.DataFrame
    prediction_rows: pd.DataFrame
    pearson_dispersion: float


def _features_for(pre: PreGamesData, games: int) -> pd.DataFrame:
    snap = pre.snapshots.set_index("games").loc[games]
    commit_time = pd.Timestamp(snap["commit_datetime"])
    cutoff = pd.Timestamp(snap["forecast_cutoff_utc"])
    if not commit_time < cutoff:
        raise ValueError(f"{games}: feature snapshot {commit_time} is not before cut-off {cutoff}")
    if games == PREDICTION_GAMES and not cutoff <= DEADLINE_UTC:
        raise ValueError("2026 features must come from before the competition deadline")
    f = pre.features[pre.features["games"] == games].set_index("nation")
    f = f.loc[pre.nations["nation"], ["population", "gdp_usd"]].copy()
    # Documented rule: a GDP still missing after walking back through earlier
    # pre-cut-off snapshots is set to population x the median GDP per head of
    # all other nations in the same snapshot. Decided before any scoring and
    # applies only to tiny territories (see LEAKAGE_AUDIT.md).
    missing = f["gdp_usd"].isna()
    median_pc = (f.loc[~missing, "gdp_usd"] / f.loc[~missing, "population"]).median()
    f["gdp_imputed"] = missing.astype(int)
    f.loc[missing, "gdp_usd"] = f.loc[missing, "population"] * median_pc
    if f[["population", "gdp_usd"]].isna().any().any() or (f[["population", "gdp_usd"]] <= 0).any().any():
        raise ValueError(f"{games}: invalid feature values")
    f["log_pop"] = np.log(f["population"])
    f["log_gdp"] = np.log(f["gdp_usd"])
    f["games"] = games
    return f


def population_gdp_model(pre: PreGamesData) -> PopGdpFit:
    rows = []
    for g in TRAINING_GAMES:
        if g >= PREDICTION_GAMES:
            raise ValueError("training Games must precede the predicted Games")
        f = _features_for(pre, g)
        took_part = pre.nations.set_index("nation")[f"participated_{g}"] == 1
        golds = complete_table(pre.medals[g], pre.nations)["gold"]
        f = f.loc[took_part[took_part].index].copy()
        f["gold"] = golds.loc[f.index]
        rows.append(f)
    train = pd.concat(rows)
    X = pd.get_dummies(train["games"].astype(str), prefix="games", dtype=float)
    X = pd.concat([X, train[["log_pop", "log_gdp"]]], axis=1)
    model = sm.GLM(train["gold"], X, family=sm.families.Poisson()).fit()

    pred = _features_for(pre, PREDICTION_GAMES)
    score = pred["log_pop"] * model.params["log_pop"] + pred["log_gdp"] * model.params["log_gdp"]
    score.name = "score"
    coefs = pd.DataFrame({"estimate": model.params, "std_error": model.bse})
    return PopGdpFit(
        ranks=rank_from_score(score),
        score=score,
        coefficients=coefs,
        training_rows=train,
        prediction_rows=pred,
        pearson_dispersion=float(model.pearson_chi2 / model.df_resid),
    )
