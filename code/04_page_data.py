"""Compact files for the interactive page: data/page/mps.json and data/page/places.json, and a copy
of the nation outlines (data/nations.geojson) from the sister project."""
import json, math, os, shutil, sys
import pandas as pd
sys.path.insert(0, '/home/claude/hist/mp-localness/code')
from common import *

os.makedirs(OUT + 'page', exist_ok=True)
T = pd.read_csv(WORK + 'mp_elections_analysed.csv.gz')
people = pd.read_csv(WORK + 'people.csv').set_index('person')
ELECTIONS = list(dict.fromkeys(T['election']))
FAMS = ['CON', 'LAB', 'LIB', 'IRN', 'LU', 'SNP', 'PC', 'ULS', 'SF', 'PEEL', 'ALLY', 'GRN', 'REF', 'SPK', 'OTH', '']
NATC = {'England': 'E', 'Wales': 'W', 'Scotland': 'S', 'Northern Ireland': 'N', 'Ireland': 'I', 'Crown Dependencies': 'C'}

seats = T.drop_duplicates('seat')[['seat', 'seat_label', 'seat_lon', 'seat_lat', 'seat_nation', 'seat_county']].reset_index(drop=True)
SI = {q: i for i, q in enumerate(seats.seat)}
pp = T.drop_duplicates('person').person.tolist()
PI = {q: i for i, q in enumerate(pp)}


def nn(x):
    return None if (x is None or (isinstance(x, float) and math.isnan(x))) else x

P = []
for q in pp:
    r = people.loc[q]
    known = nn(r.bp_lon) is not None
    if known:
        nat = NATC.get(nn(r.bp_nation), 'A')
        lon_ = round(float(r.bp_lon), 3); lat_ = round(float(r.bp_lat), 3)
    else:
        nat = ''; lon_ = lat_ = None
    src = {'wikidata P19': 'w', 'wikidata P19 (coordinates of the containing place)': 'w', 'English Wikipedia infobox': 'i',
           'English Wikipedia article text': 't'}.get(r.bp_source, '')
    lbl = nn(r.bp_label) or ''
    if r.bp_precision == 'coarse':
        src = 'c'  # named but too coarse to place
    P.append([nn(r['name']) or '', lbl, lon_, lat_, nat, src, 1 if nn(r.bp_county) == 'Greater London' else 0, q])

E = []
for e in ELECTIONS:
    d = T[T.election == e]
    rows = []
    for r in d.itertuples():
        dist = nn(r.dist_km)
        sc = nn(r.same_county)
        rows.append([SI[r.seat], PI[r.person], FAMS.index(r.family if isinstance(r.family, str) else ''),
                     None if dist is None else int(round(dist)), None if sc is None else int(sc)])
    E.append(dict(e=e, rows=rows))

out = dict(elections=ELECTIONS, fams=FAMS,
           seats=[[r.seat_label, round(r.seat_lon, 3), round(r.seat_lat, 3), r.seat_nation, nn(r.seat_county) or '', r.seat] for r in seats.itertuples()],
           people=P, E=E)
json.dump(out, open(OUT + 'page/mps.json', 'w'), separators=(',', ':'), ensure_ascii=False)

pl = json.load(open('/home/claude/hist/elections-since-1832/data/page/places.json'))
keep = [p for p in pl if p[3] >= 2]
json.dump(keep, open(OUT + 'page/places.json', 'w'), separators=(',', ':'), ensure_ascii=False)
shutil.copy(NATIONS, OUT + 'nations.geojson')
shutil.copy(COUNTIES, OUT + 'counties.geojson')  # the county map used for the same-county test
for f in ['mps.json', 'places.json']:
    print(f, os.path.getsize(OUT + 'page/' + f))
