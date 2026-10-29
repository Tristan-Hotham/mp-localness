"""Check the two Wikipedia fallbacks against Wikidata P19.

For a random sample of 400 MPs who have a precise Wikidata birthplace, I took the English Wikipedia
infobox birth_place and the first linked place after "born" in the article text, exactly as the
fallbacks do for MPs without P19, and compared the points. Adds results['validation'].
"""
import gzip, json, math, sys
import pandas as pd
sys.path.insert(0, '/home/claude/hist/mp-localness/code')
from common import *
import importlib.util

V = json.load(gzip.open('/home/claude/hist/_data18/mp-localness/mplocal_validation_v1.json.gz'))
X = json.load(gzip.open('/home/claude/hist/_data18/mp-localness/mplocal_text_places_v1.json.gz'))
people = pd.read_csv(WORK + 'people.csv').set_index('person')
PLC = pd.concat([tsv(t) for t in X['places']]).fillna('')
PLC['types'] = PLC['types'].map(lab)

# reuse the classification in 01_build (COARSE/SETTLE sets) without rerunning it
src = open(ROOT + 'code/01_build.py').read()
ns = {'lab': lab, 'point': point, 'pd': pd}
exec(src[src.index('COARSE = {'):src.index('BP = bp_table(PLC)')], ns)
BP = ns['bp_table'](PLC)


def hav(a, b):
    R = 6371.0088
    p1, p2 = math.radians(a[1]), math.radians(b[1])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[0] - a[0]) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def first_point(titles, resolver):
    for t in titles:
        r = resolver.get(t)
        if r and r.get('q') in BP and BP[r['q']]['lon'] is not None and not BP[r['q']]['coarse']:
            return (BP[r['q']]['lon'], BP[r['q']]['lat'])
    return None

out = {}
for kind in ['infobox', 'text']:
    d = []
    for p in V['sample']:
        if p not in people.index or not isinstance(people.loc[p, 'bp_source'], str) or not people.loc[p, 'bp_source'].startswith('wikidata P19'):
            continue
        if pd.isna(people.loc[p, 'bp_lon']):
            continue
        ref = (people.loc[p, 'bp_lon'], people.loc[p, 'bp_lat'])
        if kind == 'infobox':
            pt = first_point(V['links'].get(p, []) or [], V['resolve'])
        else:
            t = X['text_val'].get(p)
            pt = first_point([t.get('first') or t['link']], {**X['text_resolve'], **V['resolve']}) if t else None
        if pt:
            d.append(hav(ref, pt))
    s = pd.Series(d)
    out[kind] = dict(sample=len(V['sample']), compared=int(len(s)), within5=round(100 * (s <= 5).mean(), 1),
                     within25=round(100 * (s <= 25).mean(), 1), median_km=round(float(s.median()), 1) if len(s) else None)
print(out)
res = json.load(open(OUT + 'results.json'))
res['validation'] = out
json.dump(res, open(OUT + 'results.json', 'w'), indent=1, ensure_ascii=False)

# 2024 list against the UK Parliament Members API (current members on 29 October 2026)
import re, unicodedata
B = bundle()
def nk(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\(.*?\)|\b(sir|dame|dr|mr|mrs|ms|miss|rt|hon|mp|kc|cbe|obe|mbe)\b', ' ', s)
    w = re.sub(r'[^a-z ]', ' ', s).split()
    return (w[0], w[-1]) if w else ('', '')
T = pd.read_csv(OUT + 'mp_elections.csv')
wd = T[T.election == '2024']
api = pd.DataFrame(B['members'])
wl = set(wd.name.map(lambda s: nk(s)[1])); al = set(api.name.map(lambda s: nk(s)[1]))
api['hit'] = api.name.map(lambda s: nk(s)[1] in wl)
res = json.load(open(OUT + 'results.json'))
res['members_api_check'] = dict(wikidata_2024=int(len(wd)), api_current=int(len(api)), api_surname_found=int(api.hit.sum()),
                                api_surname_found_pct=round(100 * api.hit.mean(), 1))
json.dump(res, open(OUT + 'results.json', 'w'), indent=1, ensure_ascii=False)
print(res['members_api_check']); print(api[~api.hit].name.tolist()[:20])
