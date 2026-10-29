# Born and bred? How local are MPs, 1832 to 2024

Where MPs were born, set against the seats they won: every member returned at the 49 UK general elections from 1832 to 2024 (31,737 returns of 10,094 people), with the straight-line distance from birthplace to seat, whether the birthplace is in the seat's county, and whether the MP was born in London or abroad. Interactive map with a year slider, lines home for every MP, a seat history for every constituency and charts by era, party, nation and region.

**Interactive version:** https://maps.tristanhotham.com/mp-localness/

**Paper:** https://doi.org/10.5281/zenodo.23763155

This repository holds the interactive page, the datasets, the computed results and the analysis code for a data study by Dr Tristan Hotham (Independent researcher).

## Definitions

- **Unit**: an MP returned at a general election (someone who sat for three Parliaments counts three times). By-election entrants count only from the next general election they won.
- **Distance**: great-circle km from the birthplace point to the seat point.
- **Within 25 km**: born within 25 km of the seat point.
- **Same county**: birthplace and seat point fall in the same county on one fixed modern map for all years (ceremonial counties in England, preserved counties in Wales, council areas in Scotland, Northern Ireland as one unit). Seats in what is now the Republic of Ireland (before 1922) are left out of this measure.
- **Born in London**: birthplace inside today's Greater London.
- **Born abroad**: birthplace outside the United Kingdom, Ireland, the Isle of Man and the Channel Islands.
- Shares are of MPs whose birthplace could be placed; coverage is reported for every election.

## Headline results

- At every general election from 1832 to 2005, between 21.1% and 33.4% of placed MPs were born in their seat's county (25.9% in 1832, 27.0% in 1950, 27.9% in 1997).
- Since 2010 the share has risen: 29.6% (2010), 32.8% (2017), 35.7% (2019) and 41.9% (2024). Born within 25 km rose from 28.8% to 43.4%; the median distance fell from 82.7 km to 35.8 km.
- New MPs (each person counted once, at their first general election win): 28.4% of those first elected 1983 to 2005 were born within 25 km of their seat, 41.4% of those first elected 2010 to 2019 and 47.8% of the 2024 intake (only 57.5% of that intake placed).
- Parties, 1997 to 2024: 37.7% of Labour MPs were born in their seat's county, 18.7% of Conservatives, 31.0% of Liberal Democrats and 34.4% of SNP MPs. Conservative: 12.6% (1983 to 2005) to 22.1% (2010 to 2019); Labour: 33.5% to 41.7%, and 48.7% in 2024.
- Regions, 2010 to 2024: 53.6% of North East MPs were born in their seat's county; in the East of England 14.7%, with 34.5% born in London.
- London-born MPs: 28.2% in 1832, between 16.2% and 20.1% at every election since 1992. Born abroad: 5.7% of all returns; 300 people, of whom 88 were born in continental Europe and 71 in South Asia.
- Coverage: a birthplace could be placed for 30.7% of MPs in 1832, 58.7% in 1950, 89.2% to 95.5% from 1997 to 2019 and 72.6% in 2024. If every missing MP in 2024 were local, or none were, the 2024 county share would be 57.8% or 30.5%.

## Files

- `index.html`: the interactive page. Loads `data/page/mps.json`, `data/page/places.json`, `data/nations.geojson` and `data/counties.geojson`.
- `header.png`: social card (1200 by 630).
- `data/mp_elections.csv`: one row per MP returned at a general election (31,737 rows): election, Wikidata person and constituency items, name, seat nation, county and region, party family (and source), whether a birthplace is placed, distance, within 25 km, same county, born in London, born abroad, born in Ireland, same nation, world region for those born abroad.
- `data/people.csv`: one row per person (10,094): Wikidata item, name, sex as recorded in Wikidata, birthplace item, label and point, nation and county of the birthplace, source of the birthplace and its precision ("place" or "coarse" for a county or country).
- `data/seats.csv`: one row per constituency item: point, nation, county, region, first and last election, returns, placed returns, median distance, within 25 km and same county shares, and where the point came from.
- `data/by_election.csv`, `data/by_election_new_members.csv`, `data/by_party_family_era.csv`, `data/by_nation_era.csv`, `data/by_region_since2010.csv`: summary tables.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `data/page/`: compact files for the page. `data/nations.geojson` and `data/counties.geojson`: the outlines used (copied from earlier projects, see Sources).
- `code/`: the analysis, run in order (below).
- `release/`: the paper (PDF, LaTeX source and figures), the blog post and figures, and the Zenodo files.
- `reddit/`: the collage, its script and the post text.

## How to rerun

The scripts read the source bundles in place (retrieved 29 October 2026, paths in `code/common.py`): `mplocal_bundle_v1.json.gz` (Wikidata query results, Wikipedia infobox birth places, UK Parliament Members API current members), `mplocal_text_places_v1.json.gz` (Wikipedia article-text birth places and the place table), `mplocal_validation_v1.json.gz` (validation sample) and `mplocal_labels_fix_v1.json` (16 labels held only as "mul" or "en-gb"), plus three files from earlier projects read in place: the constituency points, contests and candidates of `elections-since-1832` and the county outlines of `bread-rolls`.

```
python3 code/01_build.py        # MPs per general election, birthplaces, seat points, party families
python3 code/02_analyse.py      # results.json and the tables
python3 code/03_validate.py     # Wikipedia fallbacks against Wikidata; 2024 list against the Members API
python3 code/04_page_data.py    # page files
python3 code/05_build_site.py   # index.html from code/page_template.html
python3 code/06_figures.py      # header.png, paper and blog figures
python3 release/paper/build_paper.py
python3 release/build_release.py
```

It needs Python 3 with pandas, numpy, shapely and matplotlib, and xelatex for the paper.

## Method in brief

- **Members**: Wikidata "position held" statements for each Parliament of the United Kingdom whose "elected in" qualifier is a UK general election, with the constituency qualifier. 650 members for 2024; 645 of the 650 current members in the UK Parliament Members API have a surname match in that list (the rest entered at by-elections).
- **Birthplaces**: Wikidata place of birth with coordinates (4,291 people); otherwise the first linked place in the English Wikipedia infobox birth place (398) or the first linked place after "born" in the article (387). On 400 MPs with a Wikidata birthplace, the infobox method was within 5 km of it 96.3% of the time (297 compared) and the text method 94.0% (167 compared). Birthplaces recorded only as a county, country or region (459 people) count as unknown. In all 5,076 of 10,094 people (50.3%) are placed.
- **Seats**: the constituency points of the sister project Who won here? (each seat's own Wikidata coordinates for 1,014 of 2,326 items, otherwise its town or county; 301 county seats are placed at their county and nudged by the direction in their name). Distances for large county seats are therefore rough.
- **Party families**: from the sister project's results (UK Parliament and House of Commons Library), matched by seat, election and surname; 92 returns have none.
- **Bounds**: for each election, the county share if every MP without a placed birthplace were local, and if none were.

## Known limits

- Coverage is low before 1900 and favours better-known MPs; the early levels are uncertain, the long flat line less so, and the post-2010 rise rests on elections with 90% or more placed (2024: 72.6%).
- Birthplace is not upbringing or residence. Hospital births put some people in a nearby city.
- Seats are points, not boundaries. One modern county map for all years.
- The 2024 rise is partly composition: Labour, whose MPs are more often locally born, won far more seats.
- Wikidata and Wikipedia are volunteer projects and may contain errors; nothing here is a judgement on any MP.

## Sources and licences

- Wikidata (members of each Parliament with constituency and election, places of birth, place coordinates and types), via the QLever endpoint (https://qlever.cs.uni-freiburg.de/wikidata): CC0.
- English Wikipedia, MP articles (birth place in the infobox and article text, only where Wikidata has none): CC BY-SA 4.0.
- UK Parliament Members API (https://members-api.parliament.uk/): Open Parliament Licence v3.0.
- Who won here? Every UK general election since 1832 (https://maps.tristanhotham.com/elections-since-1832/, https://doi.org/10.5281/zenodo.23761425): constituency points, party families (UK Parliament and House of Commons Library results, Open Parliament Licence v3.0) and nation outlines.
- County outlines: Office for National Statistics boundaries, Open Government Licence v3.0, as simplified for the bread-rolls project. Contains OS data © Crown copyright and database right 2026.
- Base map and hill shading tiles: Esri.

The data in `data/` and the text of the page are released under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), because some birthplaces are derived from Wikipedia. Contains Parliamentary information licensed under the Open Parliament Licence v3.0. The code (`code/`, `release/` and `reddit/` scripts) is released under the MIT licence (see `LICENSE`).

## Related

- Who won here? Every UK general election since 1832: https://maps.tristanhotham.com/elections-since-1832/
- Mentioned in the House: which places does Parliament talk about? https://maps.tristanhotham.com/hansard-places/

## Citation

Hotham, T. (2026). Born and Bred? How Local Are MPs, 1832 to 2024. Zenodo. https://doi.org/10.5281/zenodo.23763155

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
