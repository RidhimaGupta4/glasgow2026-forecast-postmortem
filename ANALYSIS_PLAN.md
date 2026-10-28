# Analysis plan

**Written:** 28 October 2026, after the Glasgow 2026 Games had finished and the final medal table was public, but **before any forecast or baseline in this repository was scored**. The git history shows this file, the data and the code committed before the first commit containing results. Any change to this plan after scoring is logged at the bottom with its reason.

## 1. What is being evaluated

A forecast of the final Glasgow 2026 Commonwealth Games medal table, submitted to the Royal Statistical Society Statistics in Sport Section prediction competition before the deadline of 23:59 BST on Wednesday 22 July 2026. The Games ran from 23 July to 2 August 2026.

The original submission is optional input (`data/forecast/original_submission.csv`). Everything else runs without it.

## 2. Truth

The true ranking follows the competition rules exactly:

1. Rank by gold medals.
2. Break ties by silver, then by bronze.
3. Nations still level stay tied.

All 74 participating CGAs are ranked, including the 29 that won no medal (they are tied with each other).

## 3. Metric

The competition's Kendall's tau:

$$\tau = \frac{2}{n(n-1)}\sum_{i<j}\operatorname{sign}(R_i-R_j)\,\operatorname{sign}(S_i-S_j), \qquad n = 74$$

where $R$ is the forecast rank and $S$ the true rank. A pair tied in either ranking scores zero. The denominator is always the total number of pairs. This is **not** scipy's default tau-b; tau-b is reported only as a cross-reference.

Also reported:

- **Ceiling:** the share of pairs not tied in the truth, the best score any forecast could get.
- **Share of ceiling:** tau divided by the ceiling.

## 4. Forecasts compared

All baselines use only information that existed before the deadline. Their code receives a data object that does not contain the 2026 results (`cgpm/data.py`).

| Label | Forecast | Status |
|---|---|---|
| Original | The submitted entry, if supplied | Pre-registered; scored as submitted, never edited |
| B0 | Default entry, all nations tied | The competition's reference; tau = 0 by construction |
| B1 | Birmingham 2022 table carried forward | Specified by the brief before scoring |
| B2 | Poisson regression of golds on log population and log GDP | Specified by the brief before scoring |
| B1p | B1 counting only 2022 medals in sports on the 2026 programme | Decomposition device for the programme effect, specified here before scoring |

### B2 details (fixed before scoring, no tuning)

- **Target:** gold medals per nation per Games.
- **Model:** Poisson GLM with log link, covariates log population and log GDP (current US$, official exchange rate), and one intercept per Games to absorb programme size.
- **Training Games:** 2018 and 2022 only, the two Games with a complete Factbook snapshot from before their start. Only nations that took part in each Games.
- **2014 is excluded** because the only Factbook snapshot before 23 July 2014 covers 197 of the needed files and lacks the United Kingdom.
- **2026 prediction:** the linear predictor from the latest Factbook snapshot before the deadline (commit `8662a8b`, 17 May 2026). The Games intercept is dropped since it does not change the order.
- **No hyperparameters, no variable selection, no refitting after seeing 2026.**

### Data rules (fixed before scoring)

- **Point-in-time features:** for each Games, the newest Factbook commit before that Games' cut-off. The code refuses any snapshot whose commit time is not before the cut-off.
- **Missing GDP:** first walk back through earlier commits of the same Factbook file and take the newest non-missing value. If none exists, set GDP to population times the median GDP per head of the other nations in that snapshot. This affects only tiny territories.
- **Combined Channel Islands GDP:** where the Factbook reports one figure for Jersey and Guernsey together, split it by population.
- **Home nations:** United Kingdom figures split by ONS 2023 shares (release of 17 April 2025, before the deadline).

## 5. Uncertainty

- **Nation bootstrap**, paired across all forecasts: 10,000 resamples of the 74 nations with replacement, seed 20260722, dropping self-pairs (see `cgpm/bootstrap.py`). Report 95% percentile intervals for each tau and for each pairwise difference.
- **Permutation null:** 10,000 shuffles of each forecast's ranks, seed 20260723. Reports the chance of a score at least as high from an uninformative forecast with the same ties.

### Decision rule

A forecast is said to **beat** another only if the paired 95% interval for the difference excludes zero. Otherwise the two are **not distinguishable** on this data. No claim is based on point estimates alone.

## 6. Error decomposition

1. **Per-nation contribution:** each nation's concordant minus discordant pairs. The most negative are the biggest misses.
2. **Tiers**, defined from pre-Games information only (2022 table), never from 2026 outcomes:
   - T1: top 10 of the 2022 table.
   - T2: other 2022 medallists.
   - T3: no 2022 medal.

   For each tier pairing, report the number of pairs, the share tied in truth and the tau within it.
3. **Programme effect:** compare B1 with B1p. For each nation, report how many 2022 golds came from sports not on the 2026 programme.
4. **Host effect:** host nation's share of all golds compared with its share at the previous and next Games, for 2014–2026, plus each forecast's error for Scotland. Descriptive only: there are four host Games, so no inference.

## 7. Retrospective work

Nothing fitted after the Games is presented as a forecast. B1p and B2 were specified after the Games, using pre-deadline data only, so they are labelled **retrospective baselines**. If an improved model is ever added, it goes in a separate, clearly labelled section and is never compared with the original as if it had been available on 22 July 2026.

## Change log

- *(none yet)*
