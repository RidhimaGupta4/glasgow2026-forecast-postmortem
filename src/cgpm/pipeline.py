"""Run the whole post-mortem: build forecasts, score them, quantify
uncertainty, decompose errors, and write tables, figures and the report.

    python -m cgpm.pipeline --data data --out results

Stage order matters for leakage. Forecasts are built first from
``load_pre_games`` only; the 2026 table is loaded afterwards, for scoring.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import baselines
from .bootstrap import bootstrap_taus, percentile_interval, permutation_null
from .data import complete_table, load_outcome_2026, load_pre_games
from .decompose import biggest_misses, host_shares, programme_effect, tier_breakdown, tiers_from_2022
from .ranking import rank_from_table
from .scoring import competition_tau, concordance_matrix, pair_counts, tau_b, tau_ceiling
from .submission import load_submission

N_BOOT = 10_000
N_PERM = 10_000
SEED_BOOT = 20260722
SEED_PERM = 20260723

LABELS = {
    "original": "Original submission (pre-registered)",
    "B0": "B0 default entry (all tied)",
    "B1": "B1 Birmingham 2022 carried forward",
    "B1p": "B1p 2022, 2026-programme sports only",
    "B2": "B2 population + GDP model",
}

PRIMARY_DIFFS = [("original", "B1"), ("original", "B2"), ("original", "B1p"), ("B1p", "B1"), ("B1", "B2"), ("B1p", "B2")]


def build_forecasts(data_dir: Path) -> tuple[dict[str, pd.Series], dict]:
    pre = load_pre_games(data_dir)
    forecasts = {
        "B0": baselines.default_entry(pre),
        "B1": baselines.carry_forward_2022(pre),
    }
    b1p, filtered_table = baselines.programme_filtered_2022(pre)
    forecasts["B1p"] = b1p
    fit = baselines.population_gdp_model(pre)
    forecasts["B2"] = fit.ranks
    sub_path = Path(data_dir) / "forecast/original_submission.csv"
    if sub_path.exists():
        forecasts = {"original": load_submission(sub_path, pre.nations, Path(data_dir) / "forecast/name_aliases.csv"), **forecasts}
    extras = {"pre": pre, "b2_fit": fit, "b1p_table": filtered_table}
    return forecasts, extras


def historical_carry_forward(pre) -> pd.DataFrame:
    """How well 'last Games carried forward' scored in earlier cycles.

    Uses only pre-2026 tables. For a target Games, nations are those of the
    74 that took part in it; the forecast is the previous Games' table.
    Gives context for whether 2026 was unusually easy or hard to forecast.
    """
    rows = []
    for prev, target in [(2014, 2018), (2018, 2022)]:
        took = pre.nations[pre.nations[f"participated_{target}"] == 1]
        truth_t = rank_from_table(complete_table(pre.medals[target], took))
        pred_t = rank_from_table(complete_table(pre.medals[prev], took))
        rows.append({
            "forecast": f"{prev} table carried forward",
            "target_games": target,
            "nations": len(took),
            "tau": competition_tau(pred_t, truth_t),
            "ceiling": tau_ceiling(truth_t),
            "share_of_ceiling": competition_tau(pred_t, truth_t) / tau_ceiling(truth_t),
        })
    return pd.DataFrame(rows)


def run(data_dir: Path, out_dir: Path, make_figures: bool = True, make_report: bool = True) -> dict:
    data_dir, out_dir = Path(data_dir), Path(out_dir)
    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    forecasts, extras = build_forecasts(data_dir)      # stage 1: pre-deadline only
    pre = extras["pre"]
    outcome = load_outcome_2026(data_dir, pre.nations)  # stage 2: the result
    truth = rank_from_table(outcome)

    ceiling = tau_ceiling(truth)
    matrices = {k: concordance_matrix(v, truth) for k, v in forecasts.items()}
    boot = bootstrap_taus(matrices, N_BOOT, SEED_BOOT)

    score_rows = []
    for k, pred in forecasts.items():
        tau = competition_tau(pred, truth)
        lo, hi = percentile_interval(boot[k])
        if k == "B0":
            p_perm = np.nan  # a constant forecast cannot be permuted
        else:
            null = permutation_null(pred.to_numpy(float), truth.to_numpy(float), N_PERM, SEED_PERM)
            p_perm = float((np.sum(null >= tau) + 1) / (N_PERM + 1))
        score_rows.append({
            "forecast": k,
            "label": LABELS[k],
            "tau": tau,
            "ci95_low": lo,
            "ci95_high": hi,
            "share_of_ceiling": tau / ceiling,
            "tau_b_reference": tau_b(pred, truth) if k != "B0" else np.nan,
            "permutation_p": p_perm,
            **pair_counts(pred, truth),
        })
    scores = pd.DataFrame(score_rows)

    diff_rows = []
    for a, b in PRIMARY_DIFFS:
        if a in forecasts and b in forecasts:
            d = boot[a] - boot[b]
            lo, hi = percentile_interval(d)
            point = competition_tau(forecasts[a], truth) - competition_tau(forecasts[b], truth)
            diff_rows.append({
                "comparison": f"{a} - {b}",
                "difference": point,
                "ci95_low": lo,
                "ci95_high": hi,
                "share_of_resamples_above_zero": float(np.mean(d > 0)),
                "verdict": (f"{a} beats {b}" if lo > 0 else f"{b} beats {a}" if hi < 0 else "not distinguishable"),
            })
    diffs = pd.DataFrame(diff_rows)

    ranks = pd.DataFrame({"true_rank": truth, **{f"{k}_rank": v for k, v in forecasts.items()}})
    ranks = ranks.join(outcome)
    ranks.index.name = "nation"

    tiers = tiers_from_2022(pre.medals[2022], pre.nations)
    tier_tables = {k: tier_breakdown(v, truth, tiers) for k, v in forecasts.items() if k != "B0"}
    misses = {k: biggest_misses(v, truth, k=10) for k, v in forecasts.items() if k != "B0"}
    prog = programme_effect(pre.medals[2022], extras["b1p_table"], pre.nations)
    hosts = host_shares({**pre.medals, 2026: outcome.reset_index()})
    scot = pd.DataFrame({k: {"forecast_rank": v["Scotland"], "true_rank": truth["Scotland"],
                             "error_places": v["Scotland"] - truth["Scotland"]}
                         for k, v in forecasts.items() if k != "B0"}).T

    # B1 -> B1p: which pairs changed
    m1, m1p = matrices["B1"], matrices["B1p"]
    iu = np.triu_indices(len(truth), k=1)
    flips = pd.Series({
        "discordant_to_concordant": int(((m1[iu] == -1) & (m1p[iu] == 1)).sum()),
        "concordant_to_discordant": int(((m1[iu] == 1) & (m1p[iu] == -1)).sum()),
        "tied_to_concordant": int(((m1[iu] == 0) & (m1p[iu] == 1)).sum()),
        "tied_to_discordant": int(((m1[iu] == 0) & (m1p[iu] == -1)).sum()),
        "concordant_to_tied": int(((m1[iu] == 1) & (m1p[iu] == 0)).sum()),
        "discordant_to_tied": int(((m1[iu] == -1) & (m1p[iu] == 0)).sum()),
    })

    fit = extras["b2_fit"]
    hist = historical_carry_forward(pre)

    # ---- write tables ----
    hist.to_csv(tables_dir / "historical_carry_forward.csv", index=False)
    scores.to_csv(tables_dir / "scores.csv", index=False)
    diffs.to_csv(tables_dir / "paired_differences.csv", index=False)
    ranks.to_csv(tables_dir / "ranks_by_nation.csv")
    for k, t in tier_tables.items():
        t.to_csv(tables_dir / f"tiers_{k}.csv", index=False)
    for k, t in misses.items():
        t.to_csv(tables_dir / f"biggest_misses_{k}.csv")
    prog.to_csv(tables_dir / "programme_effect.csv")
    hosts.to_csv(tables_dir / "host_gold_shares.csv", index=False)
    scot.to_csv(tables_dir / "scotland_errors.csv")
    flips.to_frame("pairs").to_csv(tables_dir / "b1_to_b1p_pair_changes.csv")
    fit.coefficients.to_csv(tables_dir / "b2_coefficients.csv")
    fit.prediction_rows.assign(score=fit.score, rank=fit.ranks).to_csv(tables_dir / "b2_features_and_scores_2026.csv")
    tiers.to_frame().to_csv(tables_dir / "tiers.csv")

    metrics = {
        "n_nations": int(len(truth)),
        "n_pairs": int(len(truth) * (len(truth) - 1) / 2),
        "tau_ceiling": ceiling,
        "pairs_tied_in_truth": int(pair_counts(truth, truth)["tied_in_truth"]),
        "zero_medal_nations": int((outcome[["gold", "silver", "bronze"]].sum(axis=1) == 0).sum()),
        "original_supplied": "original" in forecasts,
        "n_boot": N_BOOT, "seed_boot": SEED_BOOT, "n_perm": N_PERM, "seed_perm": SEED_PERM,
        "b2_training_rows": int(len(fit.training_rows)),
        "b2_pearson_dispersion": fit.pearson_dispersion,
        "b2_imputed_gdp_2026": sorted(fit.prediction_rows.index[fit.prediction_rows["gdp_imputed"] == 1].tolist()),
        "scores": scores.set_index("forecast").to_dict(orient="index"),
        "differences": diffs.set_index("comparison").to_dict(orient="index"),
        "b1_to_b1p_pair_changes": flips.to_dict(),
        "b2_coefficients": fit.coefficients.to_dict(orient="index"),
        "scotland": scot.to_dict(orient="index"),
        "historical_carry_forward": hist.set_index("target_games").to_dict(orient="index"),
        "host_gold_shares": hosts.set_index("host_games").to_dict(orient="index"),
        "tiers": {k: t.set_index("pair_type").to_dict(orient="index") for k, t in tier_tables.items()},
        "programme_effect": prog.to_dict(orient="index"),
        "ranks": ranks.to_dict(orient="index"),
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, default=float))

    if make_figures:
        from .figures import make_all
        make_all(out_dir, scores, diffs, ranks, misses, prog, hosts, tier_tables, ceiling, forecasts)
    if make_report:
        from .report import write_report
        write_report(Path(__file__).resolve().parents[2], metrics, out_dir)
    return metrics


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=Path("results"))
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--no-report", action="store_true")
    a = ap.parse_args()
    m = run(a.data, a.out, make_figures=not a.no_figures, make_report=not a.no_report)
    s = pd.DataFrame(m["scores"]).T
    print(s[["tau", "ci95_low", "ci95_high", "share_of_ceiling", "permutation_p"]].round(3).to_string())
    print(f"ceiling: {m['tau_ceiling']:.3f}")


if __name__ == "__main__":
    main()
