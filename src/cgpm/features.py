"""Point-in-time population and GDP features from CIA World Factbook snapshots.

The Factbook is mirrored on GitHub (github.com/factbook/factbook.json) with one
commit per scrape. For each Games we use the newest commit made strictly
before that Games' forecast cut-off, so every feature value is one that a
forecaster could have read on the day. The commits are pinned in
``data/reference/factbook_snapshots.csv``.

Home nations (England, Scotland, Wales, Northern Ireland) are not in the
Factbook. Their values are the United Kingdom's figure split by the shares in
ONS "Regional economic activity by GDP, UK: 1998 to 2023" (released 17 April
2025, before the 2026 cut-off). The same shares are used for every snapshot;
this is documented in LEAKAGE_AUDIT.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

_MULTIPLIERS = {
    "thousand": 1e3,
    "million": 1e6,
    "billion": 1e9,
    "trillion": 1e12,
}

_NUMBER = re.compile(
    r"\$?\s*(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<mult>thousand|million|billion|trillion)?",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\((?:[A-Za-z]+\s+)?(?P<year>(?:19|20)\d{2})\s*est\.?\)", re.IGNORECASE)


@dataclass(frozen=True)
class Parsed:
    value: float | None
    year: int | None
    raw: str


def parse_quantity(text: str | None) -> Parsed:
    """Parse Factbook strings such as '68,751,311 (2025 est.)' or
    '$3.644 trillion (2024 est.)'. Returns value=None for 'NA' or blanks.

    Only the first number in the string is used, which is the headline
    figure in the Factbook's format (later numbers are earlier years or notes).
    """
    if text is None:
        return Parsed(None, None, "")
    raw = str(text)
    head = raw.strip()
    if head.upper().startswith("NA") or head == "":
        return Parsed(None, None, raw)
    m = _NUMBER.search(head)
    if not m:
        return Parsed(None, None, raw)
    value = float(m.group("num").replace(",", ""))
    mult = m.group("mult")
    if mult:
        value *= _MULTIPLIERS[mult.lower()]
    y = _YEAR.search(head[m.start():])
    year = int(y.group("year")) if y else None
    return Parsed(value, year, raw)


def _population_text(record: dict) -> str | None:
    pop = record.get("People and Society", {}).get("Population")
    if pop is None:
        return None
    if "text" in pop:
        return pop["text"]
    # 2024+ layout: {"total": {"text": ...}, "male": ..., "female": ...}
    total = pop.get("total")
    if isinstance(total, dict):
        return total.get("text")
    return None


def _gdp_text(record: dict) -> str | None:
    gdp = record.get("Economy", {}).get("GDP (official exchange rate)")
    if gdp is None:
        return None
    return gdp.get("text")


def extract_record(record: dict) -> dict:
    pop = parse_quantity(_population_text(record))
    gdp = parse_quantity(_gdp_text(record))
    return {
        "population": pop.value,
        "population_ref_year": pop.year,
        "population_raw": pop.raw,
        "gdp_usd": gdp.value,
        "gdp_ref_year": gdp.year,
        "gdp_raw": gdp.raw,
    }


def home_nation_shares(shares: pd.DataFrame) -> pd.DataFrame:
    """Population and GDP shares of the UK for the four home nations.

    Population is implied by GDP / GDP per head (both from the same ONS
    release), so both shares come from one consistent publication.
    """
    s = shares.set_index("nation")
    uk_gdp = s.loc["United Kingdom", "gdp_2023_gbp_million"]
    uk_pop = uk_gdp * 1e6 / s.loc["United Kingdom", "gdp_per_head_2023_gbp"]
    rows = []
    for n in ["England", "Scotland", "Wales", "Northern Ireland"]:
        gdp = s.loc[n, "gdp_2023_gbp_million"]
        pop = gdp * 1e6 / s.loc[n, "gdp_per_head_2023_gbp"]
        rows.append({"nation": n, "pop_share": pop / uk_pop, "gdp_share": gdp / uk_gdp})
    out = pd.DataFrame(rows)
    return out
