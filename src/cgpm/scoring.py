"""The competition's Kendall's tau, implemented exactly as published.

The RSS rules define

    tau = 2 / (n (n - 1)) * sum_{i<j} sign(R_i - R_j) * sign(S_i - S_j)

where R is the forecast rank and S the true rank. A pair tied in either
ranking contributes zero, but the denominator is always the total number of
pairs, n(n - 1)/2. This is Kendall's tau-a extended to ties. It is NOT the
tau-b that ``scipy.stats.kendalltau`` returns by default, which divides by a
smaller, tie-corrected number. tau-b is reported only as a cross-reference.

Because tied true pairs always score zero, no forecast can reach 1 when the
true table has ties. ``tau_ceiling`` gives the best achievable score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def _aligned(pred: pd.Series, true: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    if set(pred.index) != set(true.index):
        raise ValueError("forecast and truth must cover the same nations")
    pred = pred.loc[true.index]
    if pred.isna().any() or true.isna().any():
        raise ValueError("ranks may not be missing")
    return pred.to_numpy(dtype=float), true.to_numpy(dtype=float)


def concordance_matrix(pred: pd.Series, true: pd.Series) -> np.ndarray:
    """M[i, j] = sign(R_i - R_j) * sign(S_i - S_j); +1 concordant, -1 discordant, 0 tied."""
    r, s = _aligned(pred, true)
    return np.sign(r[:, None] - r[None, :]) * np.sign(s[:, None] - s[None, :])


def competition_tau(pred: pd.Series, true: pd.Series) -> float:
    m = concordance_matrix(pred, true)
    n = m.shape[0]
    return float(m.sum() / (n * (n - 1)))  # each unordered pair counted twice in m


def tau_ceiling(true: pd.Series) -> float:
    """Highest score any forecast could get: the share of pairs not tied in truth."""
    s = true.to_numpy(dtype=float)
    n = len(s)
    untied = np.sign(s[:, None] - s[None, :]) != 0
    return float(untied.sum() / (n * (n - 1)))


def tau_b(pred: pd.Series, true: pd.Series) -> float:
    """scipy's tie-corrected tau-b, for reference only (not the competition metric)."""
    r, s = _aligned(pred, true)
    return float(stats.kendalltau(r, s, variant="b").statistic)


def pair_counts(pred: pd.Series, true: pd.Series) -> dict[str, int]:
    m = concordance_matrix(pred, true)
    upper = m[np.triu_indices(m.shape[0], k=1)]
    r, s = _aligned(pred, true)
    iu = np.triu_indices(len(s), k=1)
    true_tied = (s[iu[0]] == s[iu[1]])
    pred_tied = (r[iu[0]] == r[iu[1]])
    return {
        "pairs": int(upper.size),
        "concordant": int((upper == 1).sum()),
        "discordant": int((upper == -1).sum()),
        "tied_in_truth": int(true_tied.sum()),
        "tied_in_forecast_only": int((pred_tied & ~true_tied).sum()),
    }


def nation_contributions(pred: pd.Series, true: pd.Series) -> pd.DataFrame:
    """For each nation, its concordant and discordant pairs and net contribution.

    Every pair involves two nations, so the per-nation nets sum to twice the
    total; dividing a nation's net by n(n - 1)/2 gives its share of tau
    counted once for each member of the pair.
    """
    m = concordance_matrix(pred, true)
    idx = true.index
    out = pd.DataFrame({
        "concordant": (m == 1).sum(axis=1),
        "discordant": (m == -1).sum(axis=1),
        "net": m.sum(axis=1),
    }, index=idx)
    return out
