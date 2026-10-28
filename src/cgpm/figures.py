"""Static figures for the README and report (PNG, light surface).

Colours follow a validated categorical order (blue, orange, aqua), used only
for identity, with text in neutral ink. At most three series appear in any
chart, inside the palette's all-pairs colour-blind-safe limit, and every
multi-series chart has a legend or direct labels so colour never carries
meaning alone.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # blue, orange, aqua
NEUTRAL = "#9a9893"

SHORT = {"B1": "B1 2022 carried forward", "B1p": "B1p 2022, 2026 sports only",
         "B2": "B2 population + GDP", "B0": "B0 all tied"}


def _style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
        "text.color": INK, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.8, "axes.axisbelow": True, "legend.frameon": False,
    })


def _save(fig, path: Path):
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_scores(scores: pd.DataFrame, ceiling: float, path: Path):
    s = scores[scores["forecast"] != "B0"].iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7.2, 0.62 * len(s) + 1.6))
    y = np.arange(len(s))
    ax.hlines(y, s["ci95_low"], s["ci95_high"], color=SERIES[0], linewidth=2)
    ax.plot(s["tau"], y, "o", color=SERIES[0], markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
    for yi, row in zip(y, s.itertuples()):
        ax.text(row.ci95_high + 0.012, yi, f"{row.tau:.3f}", va="center", color=INK, fontsize=9)
    ax.axvline(ceiling, color=INK_2, linestyle="--", linewidth=1)
    ax.text(ceiling - 0.012, len(s) - 0.35, f"best possible {ceiling:.3f}", ha="right", va="bottom", color=INK_2, fontsize=8.5)
    ax.axvline(0, color=NEUTRAL, linewidth=1)
    ax.text(0.005, -0.75, "B0 all tied = 0", color=INK_2, fontsize=8.5, va="center")
    ax.set_yticks(y, [SHORT[f] for f in s["forecast"]])
    ax.set_xlim(-0.03, 1.0)
    ax.set_ylim(-1.1, len(s) - 0.1 + 0.6)
    ax.set_xlabel("Competition Kendall's tau (95% paired nation-bootstrap interval)")
    ax.set_title("How each forecast scored against the final Glasgow 2026 table", loc="left")
    ax.grid(axis="y", visible=False)
    _save(fig, path)


def fig_rank_scatter(ranks: pd.DataFrame, misses: dict, forecasts: list[str], path: Path):
    fs = [f for f in forecasts if f != "B0"]
    fig, axes = plt.subplots(1, len(fs), figsize=(3.4 * len(fs), 3.7), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, f in zip(axes, fs):
        x, yv = ranks[f"{f}_rank"], ranks["true_rank"]
        ax.plot([1, 74], [1, 74], color=NEUTRAL, linewidth=1)
        ax.scatter(x, yv, s=26, color=SERIES[0], edgecolor=SURFACE, linewidth=1, zorder=3)
        worst = (x - yv).abs().sort_values(ascending=False).head(3).index
        for k, n in enumerate(worst):
            ax.annotate(n, (x[n], yv[n]), xytext=(-14, 12 - 12 * k), textcoords="offset points", fontsize=7.5,
                        ha="right", va="center", color=INK,
                        arrowprops=dict(arrowstyle="-", color=INK_2, linewidth=0.7, shrinkA=1, shrinkB=3))
        ax.set_title(SHORT[f], loc="left", fontsize=10)
        ax.set_xlim(78, -2)
        ax.set_ylim(78, -2)
        ax.set_xlabel("Forecast rank")
    axes[0].set_ylabel("True rank (1 = top)")
    fig.suptitle("Forecast versus final rank (diagonal = exact; 29 non-medallists share true rank 46)",
                 x=0.01, y=1.04, ha="left", fontweight="bold")
    _save(fig, path)


def fig_score_lost(tier_tables: dict, path: Path):
    fs = [f for f in ["B1", "B1p", "B2"] if f in tier_tables]
    types = tier_tables[fs[0]]["pair_type"].tolist()
    short_types = [t.replace("T1 top-10 in 2022", "T1").replace("T2 other 2022 medallists", "T2")
                   .replace("T3 no 2022 medal", "T3") for t in types]
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    width = 0.8 / len(fs)
    yb = np.arange(len(types))
    for i, f in enumerate(fs):
        vals = tier_tables[f]["score_lost"].to_numpy()
        ax.barh(yb + (i - (len(fs) - 1) / 2) * width, vals, height=width - 0.04, color=SERIES[i], label=SHORT[f])
    ax.set_yticks(yb, short_types)
    ax.invert_yaxis()
    ax.set_xlabel("Score lost against the best possible (tau points)")
    ax.set_title("Where the score was lost, by pre-Games tier", loc="left")
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(axis="y", visible=False)
    fig.text(0.01, -0.04, "T1 = top 10 of the 2022 table; T2 = other 2022 medallists; T3 = no 2022 medal. "
             "Tiers use only pre-Games information.", fontsize=8, color=INK_2)
    _save(fig, path)


def fig_programme(prog: pd.DataFrame, ranks: pd.DataFrame, path: Path):
    top = prog.sort_values("golds_2022_dropped_sports", ascending=False).head(12).iloc[::-1]
    actual = ranks.set_index("nation")["gold"] if "nation" in ranks.columns else ranks["gold"]
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    y = np.arange(len(top))
    ax.hlines(y, top["golds_2022_2026_sports"], top["golds_2022_all_sports"], color=GRID, linewidth=3)
    ax.plot(top["golds_2022_all_sports"], y, "o", color=NEUTRAL, markersize=8, label="2022 golds, all sports")
    ax.plot(top["golds_2022_2026_sports"], y, "o", color=SERIES[0], markersize=8,
            label="2022 golds, sports kept for 2026")
    ax.plot(actual.loc[top.index], y, "D", color=SERIES[1], markersize=7, markeredgecolor=SURFACE,
            label="2026 golds (actual)")
    ax.set_yticks(y, top.index)
    ax.set_xscale("symlog", linthresh=5)
    ax.set_xticks([0, 2, 5, 10, 20, 40, 70], ["0", "2", "5", "10", "20", "40", "70"])
    ax.set_xlim(-0.4, 85)
    ax.set_xlabel("Gold medals (axis compressed above 5)")
    ax.set_title("The reduced programme: 2022 golds lost to dropped sports", loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=3, fontsize=8.5)
    ax.grid(axis="y", visible=False)
    _save(fig, path)


def fig_host(hosts: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    cols = ["gold_share_previous_games", "gold_share_home_games", "gold_share_next_games"]
    labels = ["Previous Games", "Home Games", "Next Games"]
    x = np.arange(len(hosts))
    w = 0.26
    for i, (c, lab) in enumerate(zip(cols, labels)):
        vals = hosts[c].to_numpy(dtype=float) * 100
        ax.bar(x + (i - 1) * w, np.nan_to_num(vals), width=w - 0.03, color=SERIES[i], label=lab)
        for xi, v in zip(x, vals):
            if np.isnan(v):
                ax.text(xi + (i - 1) * w, 0.4, "n/a", ha="center", fontsize=7.5, color=INK_2)
    ax.set_xticks(x, [f"{r.host} {r.host_games}" for r in hosts.itertuples()])
    ax.set_ylabel("Share of all golds (%)")
    ax.set_title("Host nations' share of golds before, at and after their home Games", loc="left")
    ax.legend(fontsize=8.5)
    ax.grid(axis="x", visible=False)
    fig.text(0.01, -0.04, "Four host Games only: descriptive, not a test. Programme changes between Games also move these shares.",
             fontsize=8, color=INK_2)
    _save(fig, path)


def fig_historical(hist: pd.DataFrame, b1_tau: float, ceiling: float, path: Path):
    rows = hist[["target_games", "tau", "ceiling"]].copy()
    rows.loc[len(rows)] = [2026, b1_tau, ceiling]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = np.arange(len(rows))
    ax.bar(x, rows["tau"], width=0.5, color=SERIES[0])
    ax.plot(x, rows["ceiling"], "_", color=INK, markersize=30, markeredgewidth=2)
    for xi, r in zip(x, rows.itertuples()):
        ax.text(xi, r.tau / 2, f"{r.tau:.3f}\n({r.tau / r.ceiling:.0%} of best)", ha="center",
                va="center", color=SURFACE, fontsize=8.5, fontweight="bold")
        ax.text(xi + 0.32, r.ceiling, f"best {r.ceiling:.3f}", va="center", fontsize=8, color=INK_2)
    ax.set_xticks(x, [f"{int(g) - 4} -> {int(g)}" for g in rows["target_games"]])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Competition tau")
    ax.set_title("'Last Games carried forward' across three cycles", loc="left")
    ax.grid(axis="x", visible=False)
    _save(fig, path)


def make_all(out_dir: Path, scores, diffs, ranks, misses, prog, hosts, tier_tables, ceiling, forecasts):
    _style()
    fdir = Path(out_dir) / "figures"
    fdir.mkdir(parents=True, exist_ok=True)
    ranks = ranks.reset_index()
    fig_scores(scores, ceiling, fdir / "fig1_scores.png")
    fig_rank_scatter(ranks.set_index("nation"), misses, list(forecasts), fdir / "fig2_forecast_vs_true_rank.png")
    fig_score_lost(tier_tables, fdir / "fig3_score_lost_by_tier.png")
    fig_programme(prog, ranks, fdir / "fig4_programme_effect.png")
    fig_host(hosts, fdir / "fig5_host_effect.png")
    hist = pd.read_csv(Path(out_dir) / "tables/historical_carry_forward.csv")
    b1 = float(scores.set_index("forecast").loc["B1", "tau"])
    fig_historical(hist, b1, ceiling, fdir / "fig6_carry_forward_history.png")
