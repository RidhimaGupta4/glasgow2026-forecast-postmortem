# data/reference

Fixed reference information, all public before the deadline.

| File | What it holds |
|---|---|
| `nations.csv` | The 74 nations entered for Glasgow 2026: name, three-letter code, CIA World Factbook code, a home-nation flag, and whether each took part in 2014, 2018, 2022 and 2026 (71, 71, 72 and 74 nations) |
| `programme_2026.csv` | The 2026 sports with their event counts (215 events in total) and whether each was on the 2022 programme |
| `factbook_snapshots.csv` | For each Games, the forecast cut-off and the pinned Factbook git commit used for population and GDP. Every commit predates its cut-off |
| `home_nation_shares.csv` | 2023 GDP and GDP per head for England, Scotland, Wales, Northern Ireland and the UK, from the ONS release of 17 April 2025 |

## Why these choices

- **Home nations** are not in the Factbook, so their figures are the UK's split by the ONS shares. The September 2026 ONS release is after the deadline and is deliberately not used.
- **Factbook codes** are the Factbook's own two-letter file codes (for example `uk`, `as` for Australia), not ISO codes.
- **Participation:** The Gambia was absent in 2014, the Maldives in 2018, and Gabon and Togo first took part in 2026.
