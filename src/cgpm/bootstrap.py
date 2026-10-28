"""Uncertainty for the competition tau.

Nation bootstrap (paired)
    Draw 74 nations with replacement. Kendall's tau is a U-statistic over
    pairs, so a nation paired with its own copy is not a real comparison:
    those self-pairs are dropped from both numerator and denominator. With
    draw counts c, the resampled score is

        tau* = c' M c / (n^2 - sum c_i^2)

    where M is the concordance matrix (zero diagonal). With c = 1 this is
    exactly the competition tau. All forecasts use the same draws, so
    differences between forecasts get paired intervals.

    What it measures: how much the score depends on which nations happen to
    be compared, treating nations as exchangeable draws. It does not measure
    sporting luck within the Games (that needs event-level resampling, which
    is listed as a limitation).

Permutation null
    Shuffle a forecast's ranks across nations and rescore, giving the
    distribution of tau for a forecast with the same tie structure but no
    information. Used to say whether a forecast beats chance.
"""

from __future__ import annotations

import numpy as np


def bootstrap_taus(matrices: dict[str, np.ndarray], n_boot: int, seed: int) -> dict[str, np.ndarray]:
    names = list(matrices)
    n = matrices[names[0]].shape[0]
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(n, np.full(n, 1.0 / n), size=n_boot).astype(float)  # (B, n)
    denom = n * n - (counts ** 2).sum(axis=1)
    out = {}
    for name in names:
        m = matrices[name]
        if m.shape != (n, n) or np.any(np.diag(m) != 0):
            raise ValueError(f"{name}: concordance matrix must be n x n with zero diagonal")
        num = np.einsum("bi,ij,bj->b", counts, m, counts)
        out[name] = num / denom
    return out


def percentile_interval(draws: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    a = (1 - level) / 2
    lo, hi = np.quantile(draws, [a, 1 - a])
    return float(lo), float(hi)


def permutation_null(pred_ranks: np.ndarray, true_ranks: np.ndarray, n_perm: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    s = np.sign(true_ranks[:, None] - true_ranks[None, :])
    n = len(true_ranks)
    out = np.empty(n_perm)
    for b in range(n_perm):
        r = rng.permutation(pred_ranks)
        out[b] = (np.sign(r[:, None] - r[None, :]) * s).sum() / (n * (n - 1))
    return out
