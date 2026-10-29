"""All the numbers: data/results.json plus summary tables.

Definitions (applied to MPs returned at a general election with a known birthplace point):
- distance: great-circle km from the birthplace point to the seat point;
- local (25 km): born within 25 km of the seat point;
- same county: birthplace and seat point fall in the same modern county unit (ceremonial counties in
  England, preserved counties in Wales, council areas in Scotland, Northern Ireland as one unit);
  seats in what is now the Republic of Ireland (before 1922) are left out of this measure;
- born in London: birthplace inside Greater London (2025 boundary);
- born abroad: birthplace outside the United Kingdom, Ireland, the Isle of Man and the Channel Islands.
"""
import collections, gzip, json, math, sys
import numpy as np
import pandas as pd
sys.path.insert(0, '/home/claude/hist/mp-localness/code')
from common import *

T = pd.read_csv(WORK + 'mp_elections_full.csv.gz')
people = pd.read_csv(WORK + 'people.csv')
ELECTIONS = list(dict.fromkeys(T['election']))
T['ei'] = T['election'].map(ELECTIONS.index)
T['local25'] = np.where(T.dist_km.notna(), (T.dist_km <= 25).astype(float), np.nan)
K = T[T.bp_known == 1].copy()

REGION = {}
for r, cs in {
    'North East': ['Northumberland', 'Tyne and Wear', 'Durham'],
    'North West': ['Cumbria', 'Lancashire', 'Merseyside', 'Greater Manchester', 'Cheshire'],
    'Yorkshire and the Humber': ['North Yorkshire', 'West Yorkshire', 'South Yorkshire', 'East Riding of Yorkshire'],
    'East Midlands': ['Derbyshire', 'Nottinghamshire', 'Leicestershire', 'Lincolnshire', 'Northamptonshire', 'Rutland'],
    'West Midlands': ['Herefordshire', 'Shropshire', 'Staffordshire', 'Warwickshire', 'West Midlands', 'Worcestershire'],
    'East of England': ['Bedfordshire', 'Cambridgeshire', 'Essex', 'Hertfordshire', 'Norfolk', 'Suffolk'],
    'London': ['Greater London'],
    'South East': ['Berkshire', 'Buckinghamshire', 'East Sussex', 'Hampshire', 'Isle of Wight', 'Kent', 'Oxfordshire', 'Surrey', 'West Sussex'],
    'South West': ['Bristol', 'Cornwall', 'Devon', 'Dorset', 'Gloucestershire', 'Somerset', 'Wiltshire']}.items():
    for c in cs:
        REGION[c] = r
T['seat_region'] = np.where(T.seat_nation == 'England', T.seat_county.map(REGION), T.seat_nation)
K = T[T.bp_known == 1].copy()

ERAS = [(1832, 1880, '1832 to 1880'), (1885, 1910, '1885 to 1910'), (1918, 1945, '1918 to 1945'),
        (1950, 1979, '1950 to 1979'), (1983, 2005, '1983 to 2005'), (2010, 2019, '2010 to 2019'), (2024, 2024, '2024')]
def era(y):
    for a, b, l in ERAS:
        if a <= y <= b:
            return l
T['era'] = T.year.map(era); K['era'] = K.year.map(era)

FAMN = {'CON': 'Conservative', 'LAB': 'Labour', 'LIB': 'Liberal, Whig and Liberal Democrat', 'IRN': 'Irish nationalist',
        'LU': 'Liberal Unionist', 'SNP': 'SNP', 'PC': 'Plaid Cymru', 'ULS': 'Ulster unionist (from 1974)', 'SF': 'Sinn Féin',
        'PEEL': 'Peelite', 'ALLY': 'National Liberal and allies', 'OTH': 'Other', 'SPK': 'Speaker', 'GRN': 'Green', 'REF': 'Reform UK'}


def r1(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 1)


def pct(x):
    return r1(100 * x) if x is not None and not (isinstance(x, float) and math.isnan(x)) else None


def summ(df, base=None):
    """measures for a group; base = all rows of the group (for coverage)"""
    k = df[df.bp_known == 1]
    sc = k[k.same_county.notna()]
    return dict(n=int(len(base) if base is not None else len(df)), known=int(len(k)),
                coverage=pct(len(k) / len(base if base is not None else df)) if len(base if base is not None else df) else None,
                median_km=r1(k.dist_km.median()) if len(k) else None,
                local25=pct(k.local25.mean()) if len(k) else None,
                same_county=pct(sc.same_county.mean()) if len(sc) else None,
                london=pct(k.born_london.mean()) if len(k) else None,
                abroad=pct(k.born_abroad.mean()) if len(k) else None,
                ireland=pct(k.born_ireland.mean()) if len(k) else None,
                same_nation=pct(k.same_nation.mean()) if len(k) else None)

res = {}
res['n_rows'] = int(len(T)); res['n_people'] = int(T.person.nunique()); res['n_elections'] = len(ELECTIONS)
res['n_known_rows'] = int(T.bp_known.sum()); res['known_share'] = pct(T.bp_known.mean())
res['n_people_known'] = int(T[T.bp_known == 1].person.nunique())
res['people_known_share'] = pct(res['n_people_known'] / res['n_people'])
pk = people[people.person.isin(T.person)]
res['n_people_coarse'] = int((pk.bp_precision == 'coarse').sum())
res['n_people_none'] = int(pk.bp_precision.isna().sum())
res['n_people_point_by_source'] = {k: int(v) for k, v in pk[pk.bp_precision == 'place'].bp_source.str.replace(r' \(.*\)$', '', regex=True).value_counts().items()}
src = people.set_index('person').loc[T.person.unique()].bp_source.value_counts()
res['bp_source_people'] = {k: int(v) for k, v in src.items()}
res['n_seat_items'] = int(T.seat.nunique())
res['n_byelection_statements'] = int(len(pd.read_csv(WORK + 'byelection_terms.csv')))
fs = T.family_source.value_counts(); res['family_source'] = {k: int(v) for k, v in fs.items()}
sps = T.drop_duplicates('seat').seat_point_source.fillna('')
res['seat_points'] = dict(items=int(len(sps)), own=int((sps == 'wikidata P625').sum()),
                          county_nudged=int(sps.str.contains('nudged').sum()))
res['overall'] = summ(T)

# by election
res['by_election'] = []
for e in ELECTIONS:
    d = T[T.election == e]
    s = summ(d); s['election'] = e; s['year'] = int(e[-4:])
    res['by_election'].append(s)
BE = {s['election']: s for s in res['by_election']}

# bounds for same county if missing birthplaces were all local or none local (GB+NI seats)
def bounds(d):
    d = d[d.seat_county.notna()]
    k = d[(d.bp_known == 1) & d.same_county.notna()]
    n = len(d); m = n - len(k); y = k.same_county.sum()
    return dict(low=pct(y / n), high=pct((y + m) / n), point=pct(y / len(k)) if len(k) else None)
res['county_bounds'] = {e: bounds(T[T.election == e]) for e in ELECTIONS}

# new intake: each person counted at their first general-election return
first = T.sort_values('ei').drop_duplicates('person')
res['by_election_new'] = []
for e in ELECTIONS:
    d = first[first.election == e]
    s = summ(d); s['election'] = e; s['year'] = int(e[-4:])
    res['by_election_new'].append(s)

# eras
res['by_era'] = [dict(era=l, **summ(T[T.era == l])) for a, b, l in ERAS]
res['by_era_new'] = [dict(era=l, **summ(first[first.year.map(era) == l])) for a, b, l in ERAS]

# party families by era (only cells with 100+ known)
res['by_family_era'] = []
for f in ['CON', 'LIB', 'LAB', 'IRN', 'LU', 'SNP', 'PC', 'ULS', 'SF']:
    for a, b, l in ERAS:
        d = T[(T.family == f) & (T.era == l)]
        if (d.bp_known == 1).sum() >= 30:
            res['by_family_era'].append(dict(family=f, name=FAMN[f], era=l, **summ(d)))
res['by_family_2024'] = [dict(family=f, name=FAMN[f], **summ(T[(T.year == 2024) & (T.family == f)]))
                         for f in T[T.year == 2024].family.value_counts().index if (T[(T.year == 2024) & (T.family == f)].bp_known == 1).sum() >= 5]
res['by_family_since1997'] = [dict(family=f, name=FAMN[f], **summ(T[(T.year >= 1997) & (T.family == f)]))
                              for f in ['CON', 'LAB', 'LIB', 'SNP']]

# nations and regions
res['by_nation_era'] = []
for n in ['England', 'Scotland', 'Wales', 'Ireland', 'Northern Ireland']:
    for a, b, l in ERAS:
        d = T[(T.seat_nation == n) & (T.era == l)]
        if (d.bp_known == 1).sum() >= 30:
            res['by_nation_era'].append(dict(nation=n, era=l, **summ(d)))
RG = ['North East', 'North West', 'Yorkshire and the Humber', 'East Midlands', 'West Midlands', 'East of England', 'London',
      'South East', 'South West', 'Wales', 'Scotland', 'Northern Ireland']
res['by_region_since2010'] = [dict(region=r, **summ(T[(T.seat_region == r) & (T.year >= 2010)])) for r in RG]
res['by_region_1950_1979'] = [dict(region=r, **summ(T[(T.seat_region == r) & (T.year >= 1950) & (T.year <= 1979)])) for r in RG]
res['by_region_2024'] = [dict(region=r, **summ(T[(T.seat_region == r) & (T.year == 2024)])) for r in RG]

# women and men (from 1918)
res['by_sex_since1997'] = {s: summ(T[(T.sex == s) & (T.year >= 1997)]) for s in ['female', 'male']}

# born-in-nation: Scottish and Welsh seats held by members born there
res['scot_born_scot'] = {e: pct(K[(K.seat_nation == 'Scotland') & (K.election == e)].same_nation.mean()) for e in ['1832', '1906', '1950', '2005', '2024']}
res['wales_born_wales'] = {e: pct(K[(K.seat_nation == 'Wales') & (K.election == e)].same_nation.mean()) for e in ['1832', '1906', '1950', '2005', '2024']}
res['eng_seats_born_scot'] = {e: pct((K[(K.seat_nation == 'England') & (K.election == e)].bp_nation == 'Scotland').mean()) for e in ['1832', '1906', '1950', '2005', '2024']}
res['gb_seats_born_ireland'] = {e: pct(K[(K.seat_nation.isin(['England', 'Scotland', 'Wales'])) & (K.election == e)].born_ireland.mean()) for e in ['1832', '1906', '1950', '2005', '2024']}

# distance bands
bands = [(0, 10), (10, 25), (25, 50), (50, 100), (100, 200), (200, 400), (400, 1e9)]
def band_counts(d):
    d = d[d.bp_known == 1]
    out = []
    for a, b in bands:
        out.append(pct(((d.dist_km >= a) & (d.dist_km < b) & (d.born_abroad == 0)).mean()))
    out.append(pct((d.born_abroad == 1).mean()))
    return out
res['bands_labels'] = ['under 10 km', '10 to 25 km', '25 to 50 km', '50 to 100 km', '100 to 200 km', '200 to 400 km', '400 km or more', 'abroad']
res['bands'] = {l: band_counts(T[T.era == l]) for a, b, l in ERAS}

# abroad: where (all returns, people counted once)
cty = json.load(gzip.open('/home/claude/hist/_data18/mp-localness/mplocal_validation_v1.json.gz'))['countries']
cl = tsv(cty); cl['cL'] = cl['cL'].map(lab); CL = dict(zip(cl['c'], cl['cL']))
GROUP = {}
for g, names in {
    'Europe': ['France', 'Germany', 'Austrian Empire', 'Austria–Hungary', 'Russia', 'Belarus', 'Norway', 'Latvia', 'Ukraine', 'Czech Republic',
               'Romania', 'Bulgaria', 'Georgia', 'Malta', 'Hungary', 'Spain', 'Belgium', 'Sweden', 'Denmark', 'Poland', 'Lithuania', 'Italy',
               'Switzerland', 'Greece', 'Turkey', 'Portugal', 'Netherlands', 'Dutch Republic', 'Batavian Republic', 'Republic of Abkhazia', 'Russian Empire'],
    'South Asia': ['India', 'Pakistan', 'Sri Lanka', 'Bangladesh'],
    'Africa': ['Liberia', 'Malawi', 'Mauritius', 'Uganda', 'Kenya', 'Ghana', 'South Africa', 'Egypt', 'Tanzania', 'Zambia', 'Zimbabwe'],
    'The Americas': ['Canada', 'United States', 'Guyana', 'Trinidad and Tobago', 'Jamaica', 'Grenada', 'Uruguay', 'Haiti'],
    'Australia and New Zealand': ['Australia', 'New Zealand'],
    'Rest of Asia and the Middle East': ['Pahlavi Iran', 'Qajar Iran', 'Iran', "People's Republic of China", 'Japan', 'Indonesia', 'Iraq', 'Yemen']}.items():
    for n in names:
        GROUP[n] = g
def abroad_group(r):
    for q in str(r.bp_cty).split('|'):
        if CL.get(q) in GROUP:
            return GROUP[CL[q]]
    lon, lat = r.bp_lon, r.bp_lat  # British territories labelled United Kingdom or British Empire
    if -30 < lon < 45 and lat > 34:
        return 'Europe'
    if 60 < lon < 93 and lat < 37:
        return 'South Asia'
    if lon > 93:
        return 'Rest of Asia and the Middle East'
    if lon < -30:
        return 'The Americas'
    return 'Africa'
ab_people = people[people.person.isin(T.person) & people.bp_lon.notna() & people.bp_nation.isna()].copy()
ab_people['group'] = ab_people.apply(abroad_group, axis=1)
fy = T.groupby('person').year.min()
ab_people['first'] = ab_people.person.map(fy)
res['abroad_people'] = int(len(ab_people))
res['abroad_groups'] = {g: int(v) for g, v in ab_people.group.value_counts().items()}
res['abroad_groups_by_period'] = {}
for a, b, l in [(1832, 1914, 'first elected 1832 to 1910'), (1915, 1979, 'first elected 1918 to 1979'), (1980, 2024, 'first elected 1983 to 2024')]:
    d = ab_people[(ab_people['first'] >= a) & (ab_people['first'] <= b)]
    res['abroad_groups_by_period'][l] = {g: int(v) for g, v in d.group.value_counts().items()}
T['abroad_group'] = T.person.map(dict(zip(ab_people.person, ab_people.group)))

# seat-level: how often has a seat item returned a local member (seats with 5+ known returns)
S = []
for q, d in T.groupby('seat'):
    k = d[d.bp_known == 1]
    S.append(dict(seat=q, label=d.seat_label.iloc[0], nation=d.seat_nation.iloc[0], county=d.seat_county.iloc[0], region=d.seat_region.iloc[0],
                  lon=d.seat_lon.iloc[0], lat=d.seat_lat.iloc[0], first=int(d.year.min()), last=int(d.year.max()), returns=len(d), known=len(k),
                  median_km=r1(k.dist_km.median()) if len(k) else None, local25=pct(k.local25.mean()) if len(k) else None,
                  same_county=pct(k.same_county.mean()) if len(k) and k.same_county.notna().any() else None,
                  point_source=d.seat_point_source.iloc[0]))
S = pd.DataFrame(S)
S.to_csv(OUT + 'seats.csv', index=False)

# tables
pd.DataFrame(res['by_election']).to_csv(OUT + 'by_election.csv', index=False)
pd.DataFrame(res['by_election_new']).to_csv(OUT + 'by_election_new_members.csv', index=False)
pd.DataFrame(res['by_family_era']).to_csv(OUT + 'by_party_family_era.csv', index=False)
pd.DataFrame(res['by_nation_era']).to_csv(OUT + 'by_nation_era.csv', index=False)
pd.DataFrame(res['by_region_since2010']).to_csv(OUT + 'by_region_since2010.csv', index=False)
T.drop(columns=['ei']).to_csv(WORK + 'mp_elections_analysed.csv.gz', index=False)
T[['election', 'year', 'person', 'name', 'seat', 'seat_label', 'seat_nation', 'seat_county', 'seat_region', 'family', 'party_label', 'family_source',
   'bp_known', 'dist_km', 'local25', 'same_county', 'born_london', 'born_abroad', 'born_ireland', 'same_nation', 'abroad_group']].to_csv(OUT + 'mp_elections.csv', index=False)
pk = people[people.person.isin(T.person)]
pk[['person', 'name', 'sex', 'bp', 'bp_label', 'bp_lon', 'bp_lat', 'bp_nation', 'bp_county', 'bp_source', 'bp_precision']].to_csv(OUT + 'people.csv', index=False)

# headline helper values
h = {}
for e in ['1832', '1906', '1950', '1979', '1997', '2010', '2017', '2019', '2024']:
    h[e] = BE[e]
res['h'] = h
e1950 = summ(T[(T.year >= 1950) & (T.year <= 2005)])
res['long_flat'] = dict(same_county_min=min(BE[e]['same_county'] for e in ELECTIONS if int(e[-4:]) <= 2005),
                        same_county_max=max(BE[e]['same_county'] for e in ELECTIONS if int(e[-4:]) <= 2005),
                        y1832_2005=summ(T[T.year <= 2005]))
json.dump(res, open(OUT + 'results.json', 'w'), indent=1, ensure_ascii=False)
for k in ['overall', 'long_flat', 'h']:
    print(k, json.dumps(res[k])[:1500])
print(json.dumps(res['by_family_since1997']))
print(json.dumps(res['by_family_2024']))
print(json.dumps(res['by_region_since2010']))
print(res['abroad_groups'], res['abroad_groups_by_period'])
print({e: res['county_bounds'][e] for e in ['1832', '1950', '2019', '2024']})
print(res['scot_born_scot'], res['wales_born_wales'], res['eng_seats_born_scot'], res['gb_seats_born_ireland'])
print(json.dumps(res['by_era_new']))
