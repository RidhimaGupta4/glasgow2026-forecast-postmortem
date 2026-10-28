# Data sources

All files retrieved on 28 October 2026 unless stated.

## Medal tables (`data/raw/`)

| File | Source | Check |
|---|---|---|
| `medals_2026.csv` | [2026 Commonwealth Games medal table](https://en.wikipedia.org/wiki/2026_Commonwealth_Games_medal_table), Wikipedia | Totals 216 / 215 / 243 over 45 entries match the page's totals row. Top six cross-checked against [Outlook India](https://www.outlookindia.com/sports/commonwealth-games-2026). England's 110 medals match [Team England](https://teamengland.org/commonwealth-games-history/glasgow-2026). |
| `medals_2022.csv` | [2022 Commonwealth Games medal table](https://en.wikipedia.org/wiki/2022_Commonwealth_Games_medal_table) | 280 / 282 / 315 over 43 entries. The page's version reflects later doping reallocations (known since 2023, so before the deadline). |
| `medals_2018.csv` | [2018 Commonwealth Games medal table](https://en.wikipedia.org/wiki/2018_Commonwealth_Games_medal_table) | 275 / 276 / 289 over 43 entries |
| `medals_2014.csv` | [2014 Commonwealth Games medal table](https://en.wikipedia.org/wiki/2014_Commonwealth_Games_medal_table) | 261 / 261 / 302 over 37 entries |

### 2022 by sport (`medals_2022_by_sport.csv`)

Taken from each sport's 2022 Wikipedia article (via mirrors where the main site was unreachable). Track cycling and artistic gymnastics were built from the event-by-event medallist lists, because their articles combine disciplines.

- **Athletics, swimming:** [wiki.riteme.site mirror](https://wiki.riteme.site/wiki/Athletics_at_the_2022_Commonwealth_Games) of the Wikipedia articles.
- **Track cycling:** [Cycling at the 2022 Commonwealth Games](https://en.wikipedia.org/wiki/Cycling_at_the_2022_Commonwealth_Games). The 20 track and para-track events are listed. The women's tandem sprint B had no bronze.
- **Artistic gymnastics:** [Gymnastics at the 2022 Commonwealth Games](https://en.wikipedia.org/wiki/Gymnastics_at_the_2022_Commonwealth_Games). The 14 artistic events are listed; rhythmic events are excluded.
- **Boxing:** [mdwiki mirror](https://mdwiki.org/wiki/Boxing_at_the_2022_Commonwealth_Games).
- **Judo, weightlifting, lawn bowls:** kiwix mirror of Wikipedia (October 2023 snapshot).
- **Para powerlifting:** the medal table on the [wiki.riteme.site mirror](https://wiki.riteme.site/wiki/Powerlifting_at_the_2022_Commonwealth_Games) did not name nations. Nations were assigned from the named medallists and the table's per-row counts. The post-2023 reallocation of the men's heavyweight event (gold to Nigeria, silver to Scotland, bronze to Australia), recorded on the 2022 medal-table page, is applied.
- **3x3 basketball:** [3x3 basketball at the 2022 Commonwealth Games](https://en.wikipedia.org/wiki/3x3_basketball_at_the_2022_Commonwealth_Games).
- **Netball:** Australia gold, Jamaica silver, New Zealand bronze.

Every sport's totals match its event count (tested). No nation's per-sport sum exceeds its overall 2022 total (tested).

## Reference (`data/reference/`)

| File | Source |
|---|---|
| `nations.csv` | The 74 CGAs from [2026 Commonwealth Games](https://en.wikipedia.org/wiki/2026_Commonwealth_Games). Participation in 2014, 2018 and 2022 is from [List of participating nations](https://en.wikipedia.org/wiki/List_of_participating_nations_at_the_Commonwealth_Games), giving 71 / 71 / 72 nations, which match the published totals. The Gambia was absent in 2014 (it had left the Commonwealth), the Maldives in 2018 (likewise), and Gabon and Togo debuted in 2026. |
| `programme_2026.csv` | 10 sports, 215 events, from the 2026 Games article |
| `factbook_snapshots.csv` | Pinned commits of [factbook/factbook.json](https://github.com/factbook/factbook.json), a git mirror of the CIA World Factbook (public domain) |
| `home_nation_shares.csv` | ONS, [Regional economic activity by gross domestic product, UK: 1998 to 2023](https://ons.gov.uk/economy/grossdomesticproductgdp/bulletins/regionaleconomicactivitybygrossdomesticproductuk/1998to2023), released 17 April 2025. Later corrections (29 May and 10 October 2025) affected real or volume estimates only; the current-price GDP used here was not revised. Open Government Licence v3.0. |

## Features (`data/interim/factbook_features.csv`)

Built by `scripts/extract_factbook.py` from the pinned snapshots. It contains, for each nation and Games:

- population and GDP at the official exchange rate;
- the commit used and its date;
- the raw Factbook text;
- any rule applied (walk-back, Channel Islands split, home-nation split).

## Competition rules

[RSS Prediction Competition 2026](https://qsay.uk/posts/RSScomp2026/) (Statistics in Sport Section): truth definition, the tau formula, 74 nations, and the deadline of 23:59 on 22 July 2026.

## Context used in the report text

India's boxers won seven golds in Glasgow ([World Boxing](https://worldboxing.org/india-top-medal-table-at-glasgow-2026-commonwealth-games-with-seven-golds-and-three-silvers/)), against three in 2022 (2022 boxing table above).

## Licences

- **Wikipedia content:** CC BY-SA 4.0. The medal tables here are factual data transcribed with attribution.
- **CIA World Factbook:** public domain.
- **ONS:** Open Government Licence v3.0.
- **Code in this repository:** MIT (see `LICENSE`).
