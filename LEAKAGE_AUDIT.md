# Leakage and statistical-risk audit

Each risk below is listed with how it is controlled and where that control is checked. "Test" means it fails the test suite (`make test`) if broken.

## Data leakage

| # | Risk | Control | Checked by |
|---|---|---|---|
| L1 | A baseline uses the 2026 results | Baselines take a `PreGamesData` object that never contains the 2026 table. The 2026 table is loaded only after all forecasts are built. | Test: forecasts are rebuilt with `medals_2026.csv` deleted and must be identical (`test_forecasts_build_without_the_2026_results`) |
| L2 | Population or GDP figures published after the deadline | Point-in-time CIA Factbook snapshots, pinned by git commit. The newest commit before each cut-off is used. The 2026 snapshot is dated 17 May 2026; the deadline was 22 July 2026. The extraction script refuses any later commit. | Test: every feature row's commit time precedes its cut-off (`test_feature_snapshots_precede_cutoffs`) |
| L3 | A missing GDP filled from a later source | Walk-back uses only *older* commits of the same file, which are earlier still. | Test: `test_walked_back_values_also_precede_cutoff` |
| L4 | Home-nation split from a post-deadline release | ONS "Regional economic activity by GDP, UK: 1998 to 2023" (17 April 2025). The **1998 to 2024 release (23 September 2026) is after the deadline and is deliberately not used.** | Test: `test_ons_release_precedes_deadline` |
| L5 | Model trained on the Games it predicts | B2 is fitted on 2018 and 2022 only; 2026 is prediction-only. | Test: `test_b2_trains_only_on_past_games` |
| L6 | Hyperparameters tuned on 2026 | B2 has none: fixed covariates, fixed training Games, no selection. B1 and B1p are rules with no parameters. | Test: `test_b2_has_no_free_parameters_tuned_on_2026`; ANALYSIS_PLAN.md |
| L7 | Decomposition groups chosen using the outcome | Tiers are defined from the 2022 table only. | Code: `decompose.tiers_from_2022` |
| L8 | Analysis chosen after seeing scores (forking paths) | Plan, data and code committed before the first score (commit `Pre-scoring: ...`). Post-scoring changes are logged in the plan's change log; none alters a score, interval or verdict. | git history; ANALYSIS_PLAN.md change log |

## Statistical risks

| # | Risk | What was done |
|---|---|---|
| S1 | Wrong metric (scipy's tau-b instead of the competition's tau) | The competition formula is implemented and tested against a literal double loop on random tied data. tau-b is shown only for reference. They differ here (e.g. B1: 0.588 vs 0.713). |
| S2 | Reading tau against an impossible maximum of 1 | The ceiling (0.828 in 2026) is computed and every score is also given as a share of it. |
| S3 | Bootstrap that double-counts self-pairs | Self-pairs (a nation with its own copy) are dropped from both numerator and denominator. Test: a perfect forecast scores exactly 1 in every resample. |
| S4 | Unpaired comparisons that overstate differences | All forecasts share the same resamples; differences get paired intervals. |
| S5 | Claiming "better" from a point estimate | Decision rule fixed in advance: "beats" only if the 95% paired interval excludes zero. |
| S6 | Confusing what the interval means | Stated everywhere: the bootstrap covers variation over nations, not sporting luck within the Games. |
| S7 | Over-dispersion in the Poisson model | Pearson dispersion 2.56 is reported, with quasi-Poisson standard errors. Ranks use point estimates only, which are unaffected. |
| S8 | Overfitting / underfitting B2 | Two slopes plus a Games intercept, on 143 rows. It is a deliberately simple baseline. Its out-of-sample score (0.424) is the honest measure of fit, and it is clearly beaten by carry-forward. No attempt is made to rescue it after seeing 2026. |
| S9 | Over-interpreting the host effect | Four host Games only: reported as description, with programme changes noted as a confounder. |
| S10 | Survivorship in training data | Training rows are every nation that took part in each Games (71 in 2018, 72 in 2022), including those with zero golds, not only medallists. |
| S11 | Transcription errors in medal tables | Every table's totals are tested against the published totals. Per-sport 2022 tables are tested against event counts and against each nation's overall 2022 total. |
| S12 | Reproducibility | Seeds fixed, exact library versions pinned, and a test that a fresh run reproduces the committed tables to 1e-12. |

## Known residual approximations (not leakage)

- **Home nations in 2018 and 2022** use 2023 ONS shares. This is a slowly moving split of the UK figure and not outcome information.
- **Jersey and Guernsey:** in the 2026 Factbook they share one combined GDP figure, split by population.
- **Imputed GDP:** Norfolk Island and Saint Helena have no Factbook GDP in any snapshot, so their GDP is imputed (population × the snapshot's median GDP per head). In 2018, Montserrat and Turks and Caicos are imputed the same way.
- **Sport-level programme filter:** B1p filters whole sports, not individual events.
