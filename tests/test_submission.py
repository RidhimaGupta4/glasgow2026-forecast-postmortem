from pathlib import Path

import pandas as pd
import pytest

from cgpm.submission import SubmissionError, load_submission

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def nations():
    return pd.read_csv(DATA / "reference/nations.csv")


def _write(tmp_path, df):
    p = tmp_path / "sub.csv"
    df.to_csv(p, index=False)
    return p


def test_valid_file_loads_in_canonical_order(tmp_path, nations):
    df = pd.DataFrame({"Country": nations.nation[::-1], "Rank": range(74)})
    s = load_submission(_write(tmp_path, df), nations)
    assert list(s.index) == list(nations.nation)
    assert s["Anguilla"] == 73


def test_aliases_map_names_without_touching_ranks(tmp_path, nations):
    names = nations.nation.replace({"The Gambia": "Gambia"})
    df = pd.DataFrame({"Country": names, "Rank": 1.5})
    aliases = tmp_path / "aliases.csv"
    pd.DataFrame({"submission_name": ["Gambia"], "nation": ["The Gambia"]}).to_csv(aliases, index=False)
    s = load_submission(_write(tmp_path, df), nations, aliases)
    assert s["The Gambia"] == 1.5


@pytest.mark.parametrize("mutate", ["drop_row", "bad_rank", "duplicate", "unknown_name"])
def test_invalid_files_rejected(tmp_path, nations, mutate):
    df = pd.DataFrame({"Country": nations.nation, "Rank": range(74)}).astype({"Rank": object})
    if mutate == "drop_row":
        df = df.iloc[1:]
    elif mutate == "bad_rank":
        df.loc[0, "Rank"] = "first"
    elif mutate == "duplicate":
        df.loc[1, "Country"] = df.loc[0, "Country"]
    elif mutate == "unknown_name":
        df.loc[0, "Country"] = "Atlantis"
    with pytest.raises(SubmissionError):
        load_submission(_write(tmp_path, df), nations)
