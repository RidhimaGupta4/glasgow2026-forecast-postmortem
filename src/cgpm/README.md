# src/cgpm

| Module | Role |
|---|---|
| `data.py` | Loads and validates inputs. `load_pre_games` returns only pre-deadline data; `load_outcome_2026` is the only function that opens the 2026 results |
| `ranking.py` | Ranks a medal table by gold, then silver, then bronze, leaving full ties tied. Also ranks a continuous score |
| `scoring.py` | The competition's Kendall's tau (tied pairs score zero, denominator is all pairs), the ceiling, pair counts and per-nation contributions. tau-b is included for reference only |
| `baselines.py` | B0 all tied; B1 2022 table carried forward; B1p 2022 counting only 2026-programme sports; B2 Poisson model of golds on log population and log GDP, trained on 2018 and 2022 |
| `bootstrap.py` | Paired nation bootstrap that drops self-pairs, and a permutation null |
| `decompose.py` | Tiers from the 2022 table, score lost by tier, biggest misses, programme effect, host gold shares |
| `features.py` | Parses Factbook text into numbers, and computes the home-nation shares |
| `figures.py` | The six PNG figures in `results/figures/` |
| `report.py` | Writes `REPORT.md`; every number is read from the results |
| `dashboard.py` | Writes `docs/index.html`, the self-contained dashboard |
| `pipeline.py` | Runs everything in order: forecasts first (pre-deadline data only), then the 2026 results, then scoring, decomposition and outputs |

## Order of operations

`build_forecasts()` runs before the 2026 table is loaded, and it receives a data object that does not contain it. This ordering is the main leakage control, and `tests/test_leakage_guards.py` enforces it.
