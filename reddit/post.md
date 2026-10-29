# Reddit post

## Title

[OC] How local are UK MPs? Every MP returned at 49 general elections since 1832, joined from seat to birthplace: for 170 years about a quarter were born in their seat's county, and since 2010 it has climbed to 41.9%

## Body

I took every MP returned at a UK general election from 1832 to 2024 (31,737 returns of 10,094 people), found where each was born and measured the distance to their seat. At every election from 1832 to 2005, between 21.1% and 33.4% of MPs with a known birthplace were born in their seat's county. Since 2010 it has risen at each election, to 41.9% in 2024, and the median distance fell from 83 km to 36 km. New MPs drove it: 41.4% of those first elected 2010 to 2019 were born within 25 km of their seat, against 28.4% for 1983 to 2005. Caveat: birthplaces are known for only 30.7% of MPs in 1832 and 72.6% in 2024 (89% to 96% from 1997 to 2019), so the chart shows the possible range. Interactive map: https://maps.tristanhotham.com/mp-localness/

## Source comment

Source: Wikidata (members of each Parliament with constituency and election, places of birth and coordinates, via the QLever endpoint, CC0); English Wikipedia MP articles for birthplaces where Wikidata has none (infobox birth place or the first place linked after "born", CC BY-SA 4.0; checked against Wikidata on a sample of 400 MPs); UK Parliament Members API (current members, Open Parliament Licence v3.0); constituency points and party families from my earlier "Who won here?" dataset, built from UK Parliament and House of Commons Library results (Open Parliament Licence v3.0, doi:10.5281/zenodo.23761425); ONS county boundaries (Open Government Licence v3.0).

Tools: Python (pandas, numpy, shapely, matplotlib), Leaflet for the interactive map.

Interactive map: https://maps.tristanhotham.com/mp-localness/
Blog post: https://blog.tristanhotham.com/2026/10/29/mp-localness/
Paper: https://doi.org/10.5281/zenodo.23763155
