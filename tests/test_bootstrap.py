import numpy as np
import pandas as pd
import pytest

from cgpm.bootstrap import bootstrap_taus, percentile_interval, permutation_null
from cgpm.scoring import competition_tau, concordance_matrix


def _toy(n=30, seed=0):
    rng = np.random.default_rng(seed)
    idx = [f"n{i}" for i in range(n)]
    s = pd.Series(rng.integers(1, 8, n), index=idx, dtype=float)
    r = pd.Series(s.to_numpy() + rng.normal(0, 2, n), index=idx)
    return r, s


def test_unit_counts_reproduce_competition_tau():
    r, s = _toy()
    m = concordance_matrix(r, s)
    c = np.ones(len(s))
    n = len(s)
    assert (c @ m @ c) / (n * n - (c ** 2).sum()) == pytest.approx(competition_tau(r, s))


def test_reproducible_and_paired():
    r, s = _toy()
    m = {"a": concordance_matrix(r, s), "b": concordance_matrix(s, s)}
    b1 = bootstrap_taus(m, 500, seed=7)
    b2 = bootstrap_taus(m, 500, seed=7)
    assert np.array_equal(b1["a"], b2["a"]) and np.array_equal(b1["b"], b2["b"])
    assert b1["a"].shape == (500,)


def test_self_pairs_excluded():
    # a perfect, tie-free forecast must score exactly 1 in every resample
    idx = [f"n{i}" for i in range(15)]
    s = pd.Series(np.arange(15), index=idx, dtype=float)
    draws = bootstrap_taus({"p": concordance_matrix(s, s)}, 300, seed=3)["p"]
    assert np.allclose(draws, 1.0)


def test_bootstrap_centred_near_estimate():
    r, s = _toy(n=60, seed=5)
    draws = bootstrap_taus({"a": concordance_matrix(r, s)}, 4000, seed=11)["a"]
    lo, hi = percentile_interval(draws)
    tau = competition_tau(r, s)
    assert lo < tau < hi
    assert abs(np.mean(draws) - tau) < 0.03


def test_permutation_null_centred_on_zero():
    r, s = _toy(n=40, seed=2)
    null = permutation_null(r.to_numpy(), s.to_numpy(), 3000, seed=1)
    assert abs(null.mean()) < 0.01
