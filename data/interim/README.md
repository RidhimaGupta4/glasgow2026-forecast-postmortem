# data/interim

| File | Built by |
|---|---|
| `factbook_features.csv` | `scripts/extract_factbook.py` (or `make data`) |

Population and GDP (current US dollars, official exchange rate) for all 74 nations at three points in time: the newest CIA World Factbook snapshot before the 2018 Games, before the 2022 Games, and before the 2026 competition deadline.

## Columns

`games, nation, factbook_commit, commit_datetime_utc, factbook_file, population, population_ref_year, population_raw, gdp_usd, gdp_ref_year, gdp_raw, gdp_combined_channel_islands, note`

The `*_raw` columns keep the Factbook text exactly as published, so every parsed number can be checked. `note` records any rule that was applied.

## Rules applied (all fixed before scoring)

1. **Home nations:** UK figure times the ONS 2023 share.
2. **GDP missing in the pinned snapshot:** take the newest value from an *older* commit of the same file. Older commits are still before the cut-off.
3. **Jersey and Guernsey:** where the Factbook gives one combined GDP, split it by population.
4. **GDP still missing** (Norfolk Island and Saint Helena, plus Montserrat and Turks and Caicos in 2018): left empty here and imputed in `src/cgpm/baselines.py` as population times the snapshot's median GDP per head.

`tests/test_leakage_guards.py` checks that every snapshot and every walked-back value predates its cut-off.

Rebuilding needs git and network access. The committed file is what the analysis uses.
