"""Shared paths and loaders for the mp-localness study."""
import gzip, json, re
import pandas as pd

BUNDLE = '/home/claude/hist/_data18/mp-localness/mplocal_bundle_v1.json.gz'
PLACES = '/home/claude/hist/elections-since-1832/data/constituency_places.csv'  # read only, sister project
COUNTIES = '/home/claude/hist/bread-rolls/data/counties.geojson'  # read only, ONS-derived outlines
NATIONS = '/home/claude/hist/elections-since-1832/data/nations.geojson'  # read only
ROOT = '/home/claude/hist/mp-localness/'
OUT = ROOT + 'data/'
WORK = ROOT + 'work/'


def tsv(t):
    L = t.strip('\n').split('\n')
    h = [x.lstrip('?') for x in L[0].split('\t')]
    return pd.DataFrame([dict(zip(h, l.split('\t'))) for l in L[1:]])


def lab(s):
    if not isinstance(s, str):
        return s
    m = re.match(r'^"(.*)"(@en)?$', s)
    return m.group(1) if m else s


def point(s):
    if not isinstance(s, str) or not s.startswith('POINT('):
        return (None, None)
    a, b = s[6:-1].split()
    return float(a), float(b)


def bundle():
    return json.load(gzip.open(BUNDLE))
