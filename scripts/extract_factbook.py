"""Build data/interim/factbook_features.csv from pinned Factbook snapshots.

Needs git and network access to github.com. Run once; the output CSV is
committed so the analysis itself runs offline.

    python scripts/extract_factbook.py --workdir /tmp/factbook

For every pinned commit the script first checks that the commit's own
timestamp is earlier than the Games' forecast cut-off. It stops with an
error if not, so a post-deadline snapshot can never slip in.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cgpm.features import extract_record, home_nation_shares  # noqa: E402

REPO_URL = "https://github.com/factbook/factbook.json.git"


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", type=Path, required=True, help="where to clone the Factbook mirror")
    args = ap.parse_args()

    clone = args.workdir / "factbook.json"
    if not clone.exists():
        args.workdir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", REPO_URL, str(clone)], check=True)

    snaps = pd.read_csv(ROOT / "data/reference/factbook_snapshots.csv")
    nations = pd.read_csv(ROOT / "data/reference/nations.csv")
    shares = home_nation_shares(pd.read_csv(ROOT / "data/reference/home_nation_shares.csv")).set_index("nation")

    def latest_earlier_gdp(commit: str, path: str):
        """Walk back through older commits of the same file (all older than the
        pinned one, hence also before the cut-off) for the newest non-missing GDP."""
        history = git("log", "--format=%H %cI", commit, "--", path, cwd=clone).split("\n")
        for line in history[1:]:
            if not line.strip():
                continue
            sha, when = line.split(" ", 1)
            try:
                rec = json.loads(git("show", f"{sha}:{path}", cwd=clone))
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                continue
            f = extract_record(rec)
            if f["gdp_usd"] is not None:
                return f, sha[:7], when
        return None, None, None

    rows = []
    for snap in snaps.itertuples():
        commit_time = pd.Timestamp(git("show", "-s", "--format=%cI", snap.factbook_commit, cwd=clone).strip()).tz_convert("UTC")
        cutoff = pd.Timestamp(snap.forecast_cutoff_utc)
        if not commit_time < cutoff:
            raise SystemExit(f"Snapshot {snap.factbook_commit} ({commit_time}) is not before cut-off {cutoff}")
        listing = git("ls-tree", "-r", "--name-only", snap.factbook_commit, cwd=clone).split()
        by_code = {Path(p).stem: p for p in listing if p.endswith(".json") and "/" in p}
        for n in nations.itertuples():
            path = by_code.get(n.factbook_code)
            if path is None:
                raise SystemExit(f"{n.nation}: code {n.factbook_code} missing in {snap.factbook_commit}")
            rec = json.loads(git("show", f"{snap.factbook_commit}:{path}", cwd=clone))
            feat = extract_record(rec)
            gdp_note = str(rec.get("Economy", {}).get("GDP (official exchange rate)", {}).get("note", ""))
            notes = []
            if n.home_nation == 1:
                feat["population"] = feat["population"] * shares.loc[n.nation, "pop_share"]
                feat["gdp_usd"] = feat["gdp_usd"] * shares.loc[n.nation, "gdp_share"]
                notes.append("UK figure x ONS 2023 share")
            if feat["gdp_usd"] is None:
                old, sha, when = latest_earlier_gdp(snap.factbook_commit, path)
                if old is not None:
                    feat.update({k: old[k] for k in ("gdp_usd", "gdp_ref_year", "gdp_raw")})
                    notes.append(f"GDP missing in pinned snapshot; latest earlier value from commit {sha} ({when})")
            feat["gdp_combined_channel_islands"] = int("includes Jersey and Guernsey" in gdp_note)
            feat["note"] = "; ".join(notes)
            rows.append({
                "games": snap.games,
                "nation": n.nation,
                "factbook_commit": snap.factbook_commit,
                "commit_datetime_utc": commit_time.isoformat(),
                "factbook_file": path,
                **feat,
            })

    out = pd.DataFrame(rows)

    # Where the Factbook reports one combined GDP for Jersey and Guernsey,
    # split it between the two by their populations in the same snapshot.
    for games, grp in out.groupby("games"):
        ci = grp[grp["nation"].isin(["Jersey", "Guernsey"]) & (grp["gdp_combined_channel_islands"] == 1)]
        if len(ci) == 2:
            total = ci["gdp_usd"].iloc[0]
            pops = ci.set_index("nation")["population"]
            for idx, row in ci.iterrows():
                out.loc[idx, "gdp_usd"] = total * pops[row["nation"]] / pops.sum()
                out.loc[idx, "note"] = (row["note"] + "; " if row["note"] else "") + "combined Channel Islands GDP split by population"
        elif len(ci) == 1:
            raise SystemExit(f"{games}: only one of Jersey/Guernsey flagged as combined - check by hand")

    dest = ROOT / "data/interim/factbook_features.csv"
    out.to_csv(dest, index=False)
    missing = out[out["population"].isna() | out["gdp_usd"].isna()]
    print(f"wrote {len(out)} rows to {dest}")
    if len(missing):
        print("rows still missing a value (imputed by the documented rule in cgpm/baselines.py):")
        print(missing[["games", "nation", "population", "gdp_usd"]].to_string(index=False))


if __name__ == "__main__":
    main()
