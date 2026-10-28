import itertools

import numpy as np
import pandas as pd
import pytest

from cgpm.ranking import rank_from_score, rank_from_table
from cgpm.scoring import competition_tau, concordance_matrix, nation_contributions, pair_counts, tau_b, tau_ceiling


def brute_force_tau(r, s):
    """Literal transcription of the competition formula."""
    n = len(r)
    total = 0
    for i, j in itertools.combinations(range(n), 2):
        total += np.sign(r[i] - r[j]) * np.sign(s[i] - s[j])
    return 2 * total / (n * (n - 1))


def series(values):
    return pd.Series(values, index=[f"n{i}" for i in range(len(values))], dtype=float)


def test_perfect_and_reversed():
    s = series([1, 2, 3, 4, 5])
    assert competition_tau(s, s) == pytest.approx(1.0)
    assert competition_tau(series([5, 4, 3, 2, 1]), s) == pytest.approx(-1.0)


def test_default_entry_scores_zero():
    truth = series([1, 2, 2, 4, 5, 6])
    assert competition_tau(series([74] * 6), truth) == 0.0


def test_ties_count_zero_but_stay_in_denominator():
    # 4 nations, truth has one tied pair -> ceiling 5/6
    truth = series([1, 2, 3, 3])
    assert tau_ceiling(truth) == pytest.approx(5 / 6)
    assert competition_tau(truth, truth) == pytest.approx(5 / 6)
    # tau-b would give 1.0 here: the two metrics really differ
    assert tau_b(truth, truth) == pytest.approx(1.0)


def test_matches_brute_force_on_random_tied_data():
    rng = np.random.default_rng(0)
    for _ in range(50):
        n = rng.integers(5, 40)
        r = rng.integers(1, 10, n).astype(float)
        s = rng.integers(1, 10, n).astype(float)
        assert competition_tau(series(r), series(s)) == pytest.approx(brute_force_tau(r, s))


def test_non_integer_and_negative_ranks_allowed():
    truth = series([1, 2, 3])
    assert competition_tau(series([-5.5, 0.1, 2.0]), truth) == pytest.approx(1.0)


def test_misaligned_nations_rejected():
    with pytest.raises(ValueError):
        competition_tau(pd.Series([1.0, 2.0], index=["a", "b"]), pd.Series([1.0, 2.0], index=["a", "c"]))


def test_order_of_index_irrelevant():
    truth = series([1, 2, 3, 4])
    pred = series([2, 1, 3, 4])
    assert competition_tau(pred.iloc[::-1], truth) == pytest.approx(competition_tau(pred, truth))


def test_pair_counts_and_contributions_consistent():
    rng = np.random.default_rng(1)
    r = series(rng.integers(1, 6, 20))
    s = series(rng.integers(1, 6, 20))
    pc = pair_counts(r, s)
    n = 20
    assert pc["pairs"] == n * (n - 1) // 2
    assert competition_tau(r, s) == pytest.approx((pc["concordant"] - pc["discordant"]) / pc["pairs"])
    contrib = nation_contributions(r, s)
    assert contrib["net"].sum() == 2 * (pc["concordant"] - pc["discordant"])
    m = concordance_matrix(r, s)
    assert np.all(np.diag(m) == 0) and np.array_equal(m, m.T)


def test_rank_from_table_tiebreaks():
    t = pd.DataFrame({"gold": [13, 13, 10, 10, 10, 0, 0],
                      "silver": [17, 9, 14, 7, 4, 0, 0],
                      "bronze": [9, 17, 12, 7, 5, 0, 0]},
                     index=["India", "Scotland", "NZ", "Nigeria", "Jamaica", "X", "Y"])
    r = rank_from_table(t)
    assert list(r) == [1, 2, 3, 4, 5, 6, 6]


def test_rank_from_table_silver_then_bronze():
    t = pd.DataFrame({"gold": [1, 1, 1], "silver": [1, 1, 0], "bronze": [0, 1, 5]}, index=list("abc"))
    assert list(rank_from_table(t)) == [2, 1, 3]


def test_rank_from_score():
    assert list(rank_from_score(pd.Series([0.5, 2.0, 2.0, -1.0]))) == [3, 1, 1, 4]
