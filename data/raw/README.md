# data/raw

Medal tables transcribed from Wikipedia. Every file has the columns `nation, gold, silver, bronze` and lists only nations that won at least one medal. Nations with no medals are added as zeros by the code.

| File | Games | Entries | Gold / silver / bronze totals |
|---|---|---|---|
| `medals_2014.csv` | Glasgow 2014 | 37 | 261 / 261 / 302 |
| `medals_2018.csv` | Gold Coast 2018 | 43 | 275 / 276 / 289 |
| `medals_2022.csv` | Birmingham 2022 | 43 | 280 / 282 / 315 |
| `medals_2026.csv` | Glasgow 2026, **the outcome** | 45 | 216 / 215 / 243 |
| `medals_2022_by_sport.csv` | Birmingham 2022, the 11 sports that are on the 2026 programme | 42 nations | one row per sport and nation |

## Checks (tests/test_data_integrity.py)

- Each table's totals match the totals row of its source page.
- Every medallist is one of the nations that took part in that Games.
- Each 2022 sport's totals match its number of events (for example, boxing and judo award two bronzes per event).
- No nation's per-sport total exceeds its overall 2022 total.

## Notes

- `medals_2026.csv` is the result being forecast. Only the scoring stage reads it.
- The 2022 table reflects doping reallocations made in 2023, which were known before the deadline.
- `medals_2022_by_sport.csv` uses the sport keys in `reference/programme_2026.csv`. Track cycling and artistic gymnastics were built from event-by-event medallist lists, because their source pages combine disciplines.
