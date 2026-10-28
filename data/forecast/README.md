# Adding the original submission

This folder holds the forecast that was emailed to the RSS Statistics in Sport Section before **23:59 BST, Wednesday 22 July 2026**. The repository runs without it; once it is added, the pipeline scores it and compares it with every baseline automatically.

## Rules

1. **Use the exact file that was sent, unchanged.** If you sent more than one version, use the **last** one sent before the deadline (only that one was scored), not the one that looks best now.
2. **Never edit a rank.** If a country name differs from `data/reference/nations.csv` (e.g. "Gambia" vs "The Gambia"), add a row to `name_aliases.csv` instead.
3. **Record the evidence** in `PROVENANCE.md`: the email's sent timestamp, the attachment name, and the SHA-256 hash printed by the validator. If you have the official leaderboard score, record it too. The pipeline's tau must match it to three decimals.

## Steps

```
python scripts/validate_submission.py path/to/RSS_pred_comp_submission_NAME.csv
cp path/to/RSS_pred_comp_submission_NAME.csv data/forecast/original_submission.csv
# fill in data/forecast/PROVENANCE.md
git add -f data/forecast/original_submission.csv data/forecast/PROVENANCE.md
make all
git commit -m "Add original pre-deadline submission (sha256 ...)"
```

`original_submission.csv` is git-ignored on purpose, so it can only be committed deliberately with `git add -f`.

## If you build a better model now

Put it in a separate folder, call it **retrospective** everywhere, and never present it as if it had existed on 22 July 2026. Every choice in it was made after seeing the results.
