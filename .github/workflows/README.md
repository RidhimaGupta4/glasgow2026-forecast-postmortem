# .github/workflows

| File | Runs on | What it does |
|---|---|---|
| `ci.yml` | Every push and pull request | Installs the pinned requirements, runs the tests, reruns the pipeline, and fails if any committed result, `REPORT.md` or `docs/index.html` differs from what the code produces |
