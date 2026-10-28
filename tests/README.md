# tests

```bash
make test        # or: PYTHONPATH=src python -m pytest -q
```

| File | What it checks |
|---|---|
| `test_scoring.py` | The tau matches a literal transcription of the competition formula on random tied data; ties count zero but stay in the denominator; ranking tie-breaks |
| `test_bootstrap.py` | Unit counts reproduce the exact tau; self-pairs excluded (a perfect forecast scores 1 in every resample); seeds reproducible; permutation null centred on zero |
| `test_data_integrity.py` | Medal totals match the published totals; medallists took part; participation counts 71/71/72/74; 215 events in 2026; per-sport tables consistent; features complete |
| `test_leakage_guards.py` | Forecasts are identical with the 2026 results deleted; pre-Games code never opens the 2026 file; every snapshot and walked-back value predates its cut-off; ONS release before the deadline; B2 trains on 2018 and 2022 only |
| `test_pipeline.py` | A fresh run reproduces the committed tables to 1e-12; the report has no unfilled fields; the README's numbers match the results |
| `test_dashboard.py` | Every number in the dashboard matches `results/metrics.json`; the page loads nothing from the network |

If a data file, the README or a committed result drifts from what the code produces, a test fails.
