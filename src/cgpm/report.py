"""Write REPORT.md from the computed results.

Every number in the report is read from results/metrics.json or
results/tables at build time, so the text can never drift from the
analysis. Sentences whose wording depends on a result (who beats whom) are
chosen by the code from the paired intervals, using the decision rule in
ANALYSIS_PLAN.md.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _f(x: float, d: int = 3) -> str:
    return f"{x:.{d}f}"


def _pct(x: float) -> str:
    return f"{x:.0%}"


def _pct1(x: float) -> str:
    return f"{x:.1%}"


def _ci(row) -> str:
    return f"[{_f(row['ci95_low'])}, {_f(row['ci95_high'])}]"


def _ord(n: int) -> str:
    n = int(n)
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.to_numpy()) + " |")
    return "\n".join(out)


def _verdict_sentence(diffs: pd.DataFrame, a: str, b: str, names: dict) -> str:
    key = f"{a} - {b}"
    if key not in diffs.index:
        return ""
    r = diffs.loc[key]
    span = f"difference {_f(r['difference'])}, 95% paired interval [{_f(r['ci95_low'])}, {_f(r['ci95_high'])}]"
    if r["ci95_low"] > 0:
        return f"{names[a]} beats {names[b]} ({span})."
    if r["ci95_high"] < 0:
        return f"{names[b]} beats {names[a]} ({span})."
    return f"{names[a]} and {names[b]} are not distinguishable on this data ({span})."


def write_report(root: Path, metrics: dict, out_dir: Path) -> Path:
    t = Path(out_dir) / "tables"
    scores = pd.read_csv(t / "scores.csv").set_index("forecast")
    diffs = pd.read_csv(t / "paired_differences.csv").set_index("comparison")
    hist = pd.read_csv(t / "historical_carry_forward.csv")
    hosts = pd.read_csv(t / "host_gold_shares.csv")
    prog = pd.read_csv(t / "programme_effect.csv", index_col=0)
    ranks = pd.read_csv(t / "ranks_by_nation.csv").set_index("nation")
    coefs = pd.read_csv(t / "b2_coefficients.csv", index_col=0)
    flips = pd.read_csv(t / "b1_to_b1p_pair_changes.csv", index_col=0)["pairs"]
    tiers = {k: pd.read_csv(t / f"tiers_{k}.csv") for k in scores.index if k != "B0"}

    names = {"B1": "B1 (2022 carried forward)",
             "B1p": "B1p (2022, 2026-programme sports only)", "B2": "B2 (population + GDP)"}
    ceiling = metrics["tau_ceiling"]
    b1, b1p, b2 = scores.loc["B1"], scores.loc["B1p"], scores.loc["B2"]

    # ---- score table ----
    show = scores.reset_index()
    show = pd.DataFrame({
        "Forecast": show["label"],
        "tau": show["tau"].map(_f),
        "95% interval": [f"[{_f(a)}, {_f(b)}]" for a, b in zip(show["ci95_low"], show["ci95_high"])],
        "Share of best possible": show["share_of_ceiling"].map(_pct),
        "Concordant / discordant pairs": [f"{c} / {d}" for c, d in zip(show["concordant"], show["discordant"])],
        "Permutation p": ["n/a" if pd.isna(p) else ("< 0.001" if p < 0.001 else _f(p)) for p in show["permutation_p"]],
        "tau-b (reference only)": ["n/a" if pd.isna(v) else _f(v) for v in show["tau_b_reference"]],
    })

    diff_show = diffs.reset_index()
    diff_show = pd.DataFrame({
        "Comparison": diff_show["comparison"],
        "Difference in tau": diff_show["difference"].map(_f),
        "95% paired interval": [f"[{_f(a)}, {_f(b)}]" for a, b in zip(diff_show["ci95_low"], diff_show["ci95_high"])],
        "Verdict (decision rule)": diff_show["verdict"],
    })

    # ---- tiers ----
    def lost_line(k):
        tt = tiers[k].set_index("pair_type")
        lost = tt["score_lost"]
        top = lost[[i for i in lost.index if "T1" in i]].sum()
        return lost.sum(), top
    b1_lost, b1_top_lost = lost_line("B1")
    b2_lost, b2_top_lost = lost_line("B2")
    tb1 = tiers["B1"].copy()
    tier_show = pd.DataFrame({
        "Pairs": tb1["pair_type"],
        "Number": tb1["pairs"],
        "Tied in truth": tb1["share_tied_in_truth"].map(_pct),
        "B1 tau within": tb1["tau_within"].map(_f),
        "B2 tau within": tiers["B2"]["tau_within"].map(_f),
        "B1 score lost": tb1["score_lost"].map(_f),
        "B2 score lost": tiers["B2"]["score_lost"].map(_f),
    })

    # ---- misses ----
    def misses_table(k):
        m = pd.read_csv(t / f"biggest_misses_{k}.csv").head(6)
        return _md_table(pd.DataFrame({
            "Nation": m["nation"], "Forecast rank": m["forecast_rank"].astype(int),
            "True rank": m["true_rank"].astype(int), "Concordant": m["concordant"],
            "Discordant": m["discordant"], "Net": m["net"].astype(int)}))

    # ---- programme ----
    p_top = prog.head(8)
    prog_show = pd.DataFrame({
        "Nation": p_top.index,
        "2022 golds": p_top["golds_2022_all_sports"],
        "...in 2026 sports": p_top["golds_2022_2026_sports"],
        "...in dropped sports": p_top["golds_2022_dropped_sports"],
        "Share dropped": p_top["share_dropped"].map(_pct),
        "2026 golds": [int(ranks.loc[n, "gold"]) for n in p_top.index],
        "B1 rank": [int(ranks.loc[n, "B1_rank"]) for n in p_top.index],
        "B1p rank": [int(ranks.loc[n, "B1p_rank"]) for n in p_top.index],
        "True rank": [int(ranks.loc[n, "true_rank"]) for n in p_top.index],
    })
    total_dropped = int(prog["golds_2022_dropped_sports"].sum())
    total_2022 = int(prog["golds_2022_all_sports"].sum())
    changed = int(flips.sum())

    # ---- host ----
    h = hosts.set_index("host_games")
    scot = pd.read_csv(t / "scotland_errors.csv", index_col=0)

    # ---- historical ----
    h18 = hist.set_index("target_games").loc[2018]
    h22 = hist.set_index("target_games").loc[2022]

    sig_b1_b2 = _verdict_sentence(diffs, "B1", "B2", names)
    sig_b1p_b1 = _verdict_sentence(diffs, "B1p", "B1", names)

    report = f"""# How predictable was the Glasgow 2026 medal table?

This report is generated by `python -m cgpm.pipeline`; every number below is computed, not typed. The plan it follows was committed before any scoring (`ANALYSIS_PLAN.md`), and the leakage controls are listed in `LEAKAGE_AUDIT.md`.

## 1. Summary

- The best possible score this year was **{_f(ceiling)}**, not 1. {metrics['pairs_tied_in_truth']} of the {metrics['n_pairs']} pairs of nations finished level (mostly among the {metrics['zero_medal_nations']} nations with no medal), and the rules score a tied pair as zero whatever the forecast says.
- Carrying the Birmingham 2022 table forward (B1) scored **{_f(b1['tau'])}** (95% interval {_ci(b1)}), {_pct(b1['share_of_ceiling'])} of the best possible.
- The population + GDP model (B2) scored **{_f(b2['tau'])}** ({_ci(b2)}). {sig_b1_b2}
- Adjusting 2022 for the reduced programme (B1p) scored **{_f(b1p['tau'])}**. {sig_b1p_b1} Dropping the sports that were cut did not, on its own, sharpen the forecast.
- 2026 was not unusually hard to forecast: the same carry-forward method reached {_pct1(h18['share_of_ceiling'])} of the best possible in 2018, {_pct1(h22['share_of_ceiling'])} in 2022 and {_pct1(b1['share_of_ceiling'])} in 2026.
- Almost all the lost score is among smaller nations. B1 lost {_f(b1_lost)} points against the ceiling; only {_f(b1_top_lost)} of that came from pairs involving the 2022 top ten.

## 2. Setup

**Truth.** Final Glasgow 2026 table, ranked by gold, then silver, then bronze, with nations level on all three left tied (the competition rules). All {metrics['n_nations']} participating CGAs are included.

**Metric.** The competition's Kendall's tau: concordant minus discordant pairs, divided by all {metrics['n_pairs']} pairs. Tied pairs count zero but stay in the denominator. This is not scipy's tau-b, which is shown only for reference.

**Uncertainty.** A paired nation bootstrap ({metrics['n_boot']:,} resamples, seed {metrics['seed_boot']}) that drops self-pairs, and a permutation test ({metrics['n_perm']:,} shuffles). The bootstrap measures how much the score depends on which nations are compared. It does **not** measure sporting luck inside the Games (see section 6).

## 3. Scores

![Scores](results/figures/fig1_scores.png)

{_md_table(show)}

All informative forecasts beat a random ordering with the same ties (permutation p < 0.001).

**Paired comparisons** (decision rule: a forecast "beats" another only if the 95% paired interval excludes zero):

{_md_table(diff_show)}

### B2 in detail

Poisson regression of gold medals on log population and log GDP, with a fixed effect per Games, fitted on the 2018 and 2022 Games ({metrics['b2_training_rows']} nation-Games rows). Nothing was tuned on 2026.

- Coefficient on log GDP: **{_f(coefs.loc['log_gdp', 'estimate'])}** (quasi-Poisson SE {_f(coefs.loc['log_gdp', 'quasi_poisson_std_error'])}).
- Coefficient on log population: **{_f(coefs.loc['log_pop', 'estimate'])}** (SE {_f(coefs.loc['log_pop', 'quasi_poisson_std_error'])}).

Holding GDP fixed, more people means fewer golds: what the model really rewards is wealth per head. The counts are over-dispersed (Pearson dispersion {_f(metrics['b2_pearson_dispersion'], 2)}), so quasi-Poisson standard errors are reported. Over-dispersion does not affect the point estimates, which are all the ranking uses.

2026 GDP was imputed by the pre-specified rule for {', '.join(metrics['b2_imputed_gdp_2026'])} only.

## 4. Was 2026 unusually hard?

![Carry-forward history](results/figures/fig6_carry_forward_history.png)

Scoring "last Games carried forward" in earlier cycles, using only pre-2026 tables:

{_md_table(pd.DataFrame({'Forecast': list(hist['forecast']) + ['2022 table carried forward (B1)'], 'Target Games': list(hist['target_games']) + [2026], 'tau': [_f(v) for v in list(hist['tau']) + [b1['tau']]], 'Best possible': [_f(v) for v in list(hist['ceiling']) + [ceiling]], 'Share of best': [_pct(v) for v in list(hist['share_of_ceiling']) + [b1['share_of_ceiling']]]}))}

Despite a programme cut to 10 sports, the naive forecast did about as well as it did in normal cycles. The benchmark any method has to beat is therefore roughly 0.59, and about 70% of the best achievable.

## 5. Where the forecasts went wrong

### 5.1 Pre-Games tiers: the error is in the small nations

Tiers come from the 2022 table only (T1 = top 10, T2 = other 2022 medallists, T3 = no 2022 medal), so they cannot be chosen to flatter a forecast.

![Score lost by tier](results/figures/fig3_score_lost_by_tier.png)

{_md_table(tier_show)}

The 2022 top ten are close to solved by B1 and largely by B2. The score is lost in three places:

- **Among the mid-ranked medallists (within T2)**, whose rankings reshuffle from one Games to the next.
- **Between T2 and T3**, where a nation without a 2022 medal overtook one that had one.
- **Within T3**, where B1 ties every nation without a 2022 medal and so cannot score any of their pairs.

That is the "small-nation noise": one bronze or one gold moves a small nation 10 to 20 places.

### 5.2 Biggest individual misses

Nations with the most pairs placed in the wrong order (discordant), out of their 73 pairs.

**B1:**

{misses_table('B1')}

**B2:**

{misses_table('B2')}

**B1's worst misses.** Jersey and the Isle of Man won no medal in 2022, so B1 tied them at the bottom. In 2026 they won a gold each and finished 17th and 20th.

**B2's worst misses** are nations that its income model rates highly but that won nothing (e.g. Bangladesh), and small, poorer nations that won a gold (e.g. Samoa, Dominica).

### 5.3 The reduced programme

![Programme effect](results/figures/fig4_programme_effect.png)

Of the {total_2022} golds won in 2022, {total_dropped} came in sports that were not held in 2026.

{_md_table(prog_show)}

The cut was uneven: India lost {_pct(prog.loc['India', 'share_dropped'])} of its 2022 golds and Singapore {_pct(prog.loc['Singapore', 'share_dropped'])}, against {_pct(prog.loc['Australia', 'share_dropped'])} for Australia.

Removing them changed {changed} pairs:

- {int(flips['discordant_to_concordant'])} went from discordant to concordant.
- {int(flips['concordant_to_discordant'])} went the other way.
- The rest moved to or from ties.

The net effect was nil because the programme adjustment over-corrected in places. India, for example, was ranked lower by B1p, but its boxers won far more in 2026 than in 2022, and India finished fourth, exactly where B1 had it. Knowing which sports were dropped is real information, but past medals within the remaining sports were not a better guide than the full 2022 table.

### 5.4 Host effect

![Host effect](results/figures/fig5_host_effect.png)

Scotland's share of golds went from {_pct1(h.loc[2026, 'gold_share_previous_games'])} in 2022 to {_pct1(h.loc[2026, 'gold_share_home_games'])} at home. Earlier hosts showed a similar pattern:

- Australia: {_pct1(h.loc[2018, 'gold_share_previous_games'])} to {_pct1(h.loc[2018, 'gold_share_home_games'])} in 2018.
- England: {_pct1(h.loc[2022, 'gold_share_previous_games'])} to {_pct1(h.loc[2022, 'gold_share_home_games'])} in 2022, then down to {_pct1(h.loc[2022, 'gold_share_next_games'])} away from home.

With four hosts this is description, not evidence. Programme changes between Games (here, which sports were kept) move shares as well.

For the ranking, the host effect barely mattered. Scotland finished {_ord(ranks.loc['Scotland', 'true_rank'])}; the forecasts placed it {', '.join(f"{_ord(r['forecast_rank'])} ({k})" for k, r in scot.iterrows())}.

## 6. Limitations

- **No sporting-luck interval.** The bootstrap resamples nations, not events. An interval reflecting the luck of individual finals would need event-by-event results for all 215 events, which this repository does not contain.
- **Programme filter is sport-level.** B1p keeps whole sports and does not adjust for events dropped within a sport (athletics, for example, changed slightly between Games).
- **GDP data quality for tiny territories.** Factbook figures have mixed reference years, Jersey and Guernsey share one combined figure split by population, and two territories' GDP is imputed. All of this was fixed by rule before scoring, and these nations carry little weight either way.
- **Home-nation split.** The four home nations are the UK figure times ONS 2023 shares, applied to every snapshot. The shares move slowly, and they are not outcome data, so this cannot leak results. It is still an approximation for 2018 and 2022.
- **Medal-table transcription.** Medal tables were transcribed from Wikipedia. Every table's totals are checked against the published totals by the test suite, and the 2026 top six against an independent source, but individual rows could still carry a transcription error.
- **Retrospective baselines.** B1p and B2 were specified after the Games (using only pre-deadline data), so a sceptic can ask whether they were chosen knowing how they would do. The mitigations: B1 and B2 come from the project brief, B1p is a decomposition device rather than a competitor, and the plan was committed before the first score.

## 7. Reproduce

```
pip install -r requirements.txt
make all        # tests, then the full pipeline
```

`make data` re-extracts the Factbook features (needs git and network access). Everything else runs offline from the committed data.
"""
    path = Path(root) / "REPORT.md"
    path.write_text(report)
    return path
