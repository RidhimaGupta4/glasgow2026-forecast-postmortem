"""Where the forecasts went wrong.

Every grouping here is defined from pre-Games information (the 2022 table or
the 2026 programme), never from the 2026 outcome, so the breakdown cannot
flatter a forecast by choosing groups after the fact.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import complete_table
from .ranking import rank_from_table
from .scoring import concordance_matrix, nation_contributions

TIER_LABELS = {1: "T1 top-10 in 2022", 2: "T2 other 2022 medallists", 3: "T3 no 2022 medal"}


def tiers_from_2022(medals_2022: pd.DataFrame, nations: pd.DataFrame) -> pd.Series:
    table = complete_table(medals_2022, nations)
    r = rank_from_table(table)
    won = table[["gold", "silver", "bronze"]].sum(axis=1) > 0
    tier = pd.Series(3, index=table.index, name="tier")
    tier[won] = 2
    tier[r <= 10] = 1
    return tier


def tier_breakdown(pred: pd.Series, true: pd.Series, tier: pd.Series) -> pd.DataFrame:
    m = concordance_matrix(pred, true)
    s = true.to_numpy(dtype=float)
    t = tier.loc[true.index].to_numpy()
    n = len(s)
    total_pairs = n * (n - 1) / 2
    rows = []
    for a in (1, 2, 3):
        for b in (1, 2, 3):
            if b < a:
                continue
            ia, ib = np.where(t == a)[0], np.where(t == b)[0]
            block = m[np.ix_(ia, ib)]
            tied = np.sign(s[ia][:, None] - s[ib][None, :]) == 0
            if a == b:
                iu = np.triu_indices(len(ia), k=1)
                vals, tied_vals = block[iu], tied[iu]
            else:
                vals, tied_vals = block.ravel(), tied.ravel()
            pairs = vals.size
            rows.append({
                "pair_type": f"{TIER_LABELS[a]} vs {TIER_LABELS[b]}" if a != b else f"within {TIER_LABELS[a]}",
                "pairs": int(pairs),
                "share_tied_in_truth": float(tied_vals.mean()) if pairs else np.nan,
                "tau_within": float(vals.sum() / pairs) if pairs else np.nan,
                "contribution_to_overall_tau": float(vals.sum() / total_pairs),
            })
    return pd.DataFrame(rows)


def biggest_misses(pred: pd.Series, true: pd.Series, k: int = 10) -> pd.DataFrame:
    c = nation_contributions(pred, true)
    c["forecast_rank"] = pred.loc[c.index]
    c["true_rank"] = true.loc[c.index]
    return c.sort_values(["net", "discordant"], ascending=[True, False]).head(k)


def programme_effect(medals_2022: pd.DataFrame, filtered: pd.DataFrame, nations: pd.DataFrame) -> pd.DataFrame:
    full = complete_table(medals_2022, nations)
    out = pd.DataFrame({
        "golds_2022_all_sports": full["gold"],
        "golds_2022_2026_sports": filtered["gold"],
    })
    out["golds_2022_dropped_sports"] = out["golds_2022_all_sports"] - out["golds_2022_2026_sports"]
    with np.errstate(divide="ignore", invalid="ignore"):
        out["share_dropped"] = np.where(out["golds_2022_all_sports"] > 0,
                                        out["golds_2022_dropped_sports"] / out["golds_2022_all_sports"], np.nan)
    return out[out["golds_2022_all_sports"] > 0].sort_values("golds_2022_dropped_sports", ascending=False)


HOSTS = {2014: "Scotland", 2018: "Australia", 2022: "England", 2026: "Scotland"}


def host_shares(tables: dict[int, pd.DataFrame]) -> pd.DataFrame:
    years = sorted(tables)
    rows = []
    for y, host in HOSTS.items():
        def share(year):
            if year not in tables:
                return np.nan
            t = tables[year].set_index("nation")
            g = t["gold"].sum()
            return float(t["gold"].get(host, 0) / g)
        i = years.index(y)
        rows.append({
            "host_games": y,
            "host": host,
            "gold_share_previous_games": share(years[i - 1]) if i > 0 else np.nan,
            "gold_share_home_games": share(y),
            "gold_share_next_games": share(years[i + 1]) if i + 1 < len(years) else np.nan,
        })
    return pd.DataFrame(rows)
