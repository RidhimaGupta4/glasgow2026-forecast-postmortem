# results/tables

All files are generated; tau values use the competition's formula. B0 = all tied, B1 = 2022 carried forward, B1p = 2022 counting only 2026-programme sports, B2 = population + GDP model.

| File | Contents |
|---|---|
| `scores.csv` | Each forecast's tau, 95% bootstrap interval, share of the ceiling, permutation p-value, tau-b (reference only), and concordant, discordant and tied pair counts |
| `paired_differences.csv` | Paired bootstrap differences between forecasts, with the verdict from the pre-set decision rule |
| `ranks_by_nation.csv` | For all 74 nations: final rank, each forecast's rank, and 2026 medals |
| `tiers.csv` | Each nation's pre-Games tier (T1 = 2022 top 10, T2 = other 2022 medallists, T3 = no 2022 medal) |
| `tiers_B1.csv`, `tiers_B1p.csv`, `tiers_B2.csv` | For each tier pairing: number of pairs, share tied in truth, tau within it, contribution to tau, and score lost against the ceiling |
| `biggest_misses_B1.csv`, `biggest_misses_B1p.csv`, `biggest_misses_B2.csv` | The 10 nations with the most pairs placed in the wrong order |
| `programme_effect.csv` | For each 2022 gold-winning nation: golds in all sports, in sports kept for 2026, in dropped sports, and the share dropped |
| `b1_to_b1p_pair_changes.csv` | How many pairs changed status (concordant, discordant, tied) when moving from B1 to B1p |
| `historical_carry_forward.csv` | "Previous Games carried forward" scored for 2018 and 2022, with ceilings |
| `host_gold_shares.csv` | Host nations' share of golds at the previous, home and next Games, 2014 to 2026 |
| `scotland_errors.csv` | Each forecast's rank error for the host, Scotland |
| `b2_coefficients.csv` | B2's coefficients with Poisson and quasi-Poisson standard errors |
| `b2_features_and_scores_2026.csv` | The 2026 inputs to B2 (population, GDP, any imputation flag) with each nation's score and rank |
