"""Check a competition CSV before adding it to the repository.

    python scripts/validate_submission.py path/to/RSS_pred_comp_submission_NAME.csv

Read-only: reports problems and, if the file is valid, the SHA-256 hash to
record in data/forecast/PROVENANCE.md. It never edits the file.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cgpm.submission import SubmissionError, load_submission  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = Path(sys.argv[1])
    nations = pd.read_csv(ROOT / "data/reference/nations.csv")
    try:
        ranks = load_submission(path, nations, ROOT / "data/forecast/name_aliases.csv")
    except SubmissionError as e:
        raise SystemExit(f"INVALID: {e}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"VALID: 74 nations, ranks from {ranks.min():g} to {ranks.max():g}, "
          f"{ranks.nunique()} distinct rank values")
    print(f"sha256: {digest}")


if __name__ == "__main__":
    main()
