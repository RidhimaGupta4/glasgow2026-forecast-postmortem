# src

The analysis code, as one installable package: [`cgpm/`](cgpm/) (Commonwealth Games post-mortem).

```bash
pip install -e .                 # or: export PYTHONPATH=src
python -m cgpm.pipeline          # build forecasts, score, write results/, REPORT.md and docs/index.html
```

See [`cgpm/README.md`](cgpm/README.md) for what each module does.
