# scripts

| Script | Purpose | Needs network |
|---|---|---|
| `extract_factbook.py` | Rebuilds `data/interim/factbook_features.csv` from the pinned CIA World Factbook commits in `data/reference/factbook_snapshots.csv` | Yes (git clone of github.com/factbook/factbook.json) |

```bash
python scripts/extract_factbook.py --workdir .cache/factbook   # or: make data
```

Before reading any snapshot, the script checks that the commit's timestamp is earlier than that Games' cut-off, and it stops with an error if not. The output is committed, so you only need to run this to verify or rebuild the features.
