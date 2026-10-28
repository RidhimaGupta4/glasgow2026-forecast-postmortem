# data

Every input the analysis uses. Nothing in this folder is produced by the pipeline; it is all committed, so the analysis runs offline.

| Folder | Contents |
|---|---|
| [`raw/`](raw/) | Medal tables for 2014, 2018, 2022 and 2026, and the 2022 medals by sport |
| [`reference/`](reference/) | The 74 nations, the 2026 programme, pinned Factbook snapshots and ONS home-nation figures |
| [`interim/`](interim/) | Point-in-time population and GDP, built from the pinned snapshots |

## The one rule

Only `raw/medals_2026.csv` contains information from after the competition deadline (23:59 BST, 22 July 2026). It is read by the scoring stage only, never by a forecast. `tests/test_leakage_guards.py` deletes it and checks that every forecast is unchanged.

Sources, checks and licences for every file are in [`DATA_SOURCES.md`](../DATA_SOURCES.md).
