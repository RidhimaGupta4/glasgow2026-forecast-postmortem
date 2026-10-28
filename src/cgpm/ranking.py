"""Turning medal tables and scores into ranks.

All ranks use 1 = best and "competition" ties: tied nations share the best
rank of their group (1, 2, 2, 4, ...). Only the order matters for Kendall's
tau, so the tie convention never changes a score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rank_from_table(table: pd.DataFrame) -> pd.Series:
    """Rank by gold, then silver, then bronze. Nations level on all three stay tied.

    This is the competition's definition of the true ranking (RSS Statistics in
    Sport Section, 2026 rules).
    """
    key = list(zip(table["gold"], table["silver"], table["bronze"]))
    ranks = [1 + sum(other > k for other in key) for k in key]
    return pd.Series(ranks, index=table.index, name="rank", dtype=float)


def rank_from_score(score: pd.Series) -> pd.Series:
    """Rank from a continuous score where higher is better. Equal scores tie."""
    values = score.to_numpy(dtype=float)
    ranks = [1 + int(np.sum(values > v)) for v in values]
    return pd.Series(ranks, index=score.index, name="rank", dtype=float)
