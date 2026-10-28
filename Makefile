PY ?= python
export PYTHONPATH := src

.PHONY: all test results data clean

all: results test

test:
	$(PY) -m pytest -q

results:
	$(PY) -m cgpm.pipeline --data data --out results

# Re-extract point-in-time population/GDP from the pinned Factbook commits
# (needs git and network access; the output is committed, so this is optional)
data:
	$(PY) scripts/extract_factbook.py --workdir .cache/factbook

clean:
	rm -rf results/tables/* results/figures/* results/metrics.json .pytest_cache
