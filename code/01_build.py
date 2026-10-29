"""Build the MP-by-election table: every member returned at a UK general election, 1832 to 2024,
with seat point, birthplace point and the localness measures.

Unit of analysis: one row per member returned at a general election (Wikidata P39 statement on a
"member of the Nth Parliament of the United Kingdom" position whose P2715 "elected in" qualifier is a
UK general election). By-election entrants are kept in work/ but left out of the main table.

Birthplace: Wikidata P19 (place of birth) with its P625 coordinates; if the place has no coordinates,
the coordinates of the place it lies in (P131). If an MP has no P19, the first linked place in the
birth_place field of the English Wikipedia infobox, resolved to Wikidata. Source recorded per row.

Seat point: the constituency point from the sister project elections-since-1832
(data/constituency_places.csv, read only), else the constituency's own Wikidata coordinates.

Writes work/terms.parquet-free CSVs: data/mp_elections.csv and work/people.csv.
"""
import collections, gzip, json, math, re, sys
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
from shapely.prepared import prep
sys.path.insert(0, '/home/claude/hist/mp-localness/code')
from common import *

B = bundle()
terms = tsv(B['terms']).fillna('')
persons = tsv(B['persons']).fillna('')
bps = tsv(B['bps']).fillna('')
ibbps = tsv(B['infobox_bps']).fillna('')
dist = tsv(B['districts']).fillna('')
ges = tsv(B['ges']).fillna('')
groups = tsv(B['groups']).fillna('')

# ---------- general elections ----------
ges['geL'] = ges['geL'].map(lab)
gel = ges.drop_duplicates('ge').set_index('ge')['geL']
is_gen = ges.groupby('ge')['inst'].apply(lambda s: 'Q15283424' in set(s) or any('general election' in str(x) for x in []))
GEN = {}
for q, l in gel.items():
    m = re.match(r'^((?:January |December |February |October )?\d{4}) United Kingdom general election$', l)
    if m:
        GEN[q] = m.group(1)
ELECTIONS = ['1832', '1835', '1837', '1841', '1847', '1852', '1857', '1859', '1865', '1868', '1874', '1880',
             '1885', '1886', '1892', '1895', '1900', '1906', 'January 1910', 'December 1910', '1918', '1922',
             '1923', '1924', '1929', '1931', '1935', '1945', '1950', '1951', '1955', '1959', '1964', '1966',
             '1970', 'February 1974', 'October 1974', '1979', '1983', '1987', '1992', '1997', '2001', '2005',
             '2010', '2015', '2017', '2019', '2024']
terms['election'] = terms['ge'].map(GEN).fillna('')
print('statements', len(terms), 'with a general election', (terms.election != '').sum())
print('elections found', sorted(set(terms.election) - {''}, key=lambda e: ELECTIONS.index(e) if e in ELECTIONS else 99)[:3], len(set(terms.election) - {''}))
missing = set(ELECTIONS) - set(terms.election)
print('missing elections', missing)
gen = terms[terms.election.isin(ELECTIONS)].copy()
gen = gen.drop_duplicates(['person', 'election', 'd'])
byel = terms[terms.election == ''].copy()
byel.to_csv(WORK + 'byelection_terms.csv', index=False)

# ---------- people ----------
persons['personL'] = persons['personL'].map(lab)
_miss = sorted(set(terms.person) - set(persons.person))  # truthy-rank gaps in the person query
FIX = json.load(open('/home/claude/hist/_data18/mp-localness/mplocal_labels_fix_v1.json'))
_extra = []
for q in _miss:
    x = FIX['extra_people'].get(q, {})
    for b in (x.get('p19') or ['']):
        _extra.append(dict(person=q, personL='', dob='', sex=x.get('sex', ''), bp=b))
persons = pd.concat([persons, pd.DataFrame(_extra)], ignore_index=True)
# labels held only as 'mul' or 'en-gb' in Wikidata
persons['personL'] = [l if isinstance(l, str) and l else FIX['labels'].get(q, '') for q, l in zip(persons.person, persons.personL)]
print('people missing from the person query (birthplace unknown):', _miss)
P = persons.groupby('person').agg(name=('personL', 'first'), dob=('dob', 'first'), sex=('sex', 'first'),
                                  bps=('bp', lambda s: [x for x in dict.fromkeys(s) if x])).reset_index()

TEXTB = json.load(gzip.open('/home/claude/hist/_data18/mp-localness/mplocal_text_places_v1.json.gz'))
PLC = pd.concat([tsv(t) for t in TEXTB['places']]).fillna('')
PLC['types'] = PLC['types'].map(lab)

# place types too large to give a meaningful point (counties, countries, regions, islands) unless the
# item is also typed as a settlement; such birthplaces count as "place too coarse" (unknown point)
COARSE = {'ceremonial county of England', 'sovereign state', 'country', 'county of Ireland', 'historic county of the United Kingdom',
          'historic county of England', 'council area', 'historical country', 'registration county', 'lieutenancy area of Scotland',
          'non-metropolitan county', 'island', 'shire of Scotland', 'island country', 'peninsula', 'region', 'historic county of Wales',
          'principal area', 'administrative county', 'county of Northern Ireland', 'crown colony', 'republic', 'metropolitan county',
          'valley', 'constituent country of the United Kingdom', 'vice-county', 'disputed territory', 'Mediterranean country',
          'historical region', 'unitary authority area', 'Wikimedia disambiguation page', 'human', 'colony', 'province', 'state of the United States',
          'province of Canada', 'state of Australia', 'county', 'geographic region', 'archipelago', 'continent', 'empire', 'dominion of the British Empire'}
SETTLE = {'town', 'civil parish', 'village', 'city', 'big city', 'market town', 'area of London', 'suburb', 'human settlement', 'small burgh',
          'county town', 'largest city', 'port city', 'metropolis', 'large burgh', 'national capital', 'hamlet', 'megacity', 'global city',
          'state capital', 'post town', 'capital city', 'city of United Kingdom', 'town of the United Kingdom', 'seaside resort', 'community'}


SMALL = {'City of London', 'British Hong Kong', 'Gibraltar', 'City of Westminster'}  # small enough for a point


def bp_table(df):
    out = {}
    for q, g in df.groupby('bp'):
        own = [point(c) for c in g['coord'] if c]
        par = [point(c) for c in g['parcoord'] if c]
        ctys = sorted(set(x for x in g['cty'] if x))
        types = set(t for x in g['types'] for t in x.split('|') if t)
        coarse = bool(types & COARSE) and not (types & SETTLE) and lab(g['bpL'].iloc[0]) not in SMALL
        if own:
            lon, lat = own[0]; how = 'own'
        elif par:
            lon, lat = par[0]; how = 'parent'
        else:
            lon = lat = None; how = 'none'
        out[q] = dict(label=lab(g['bpL'].iloc[0]), lon=lon, lat=lat, how=how, cty='|'.join(ctys), coarse=coarse, types='|'.join(sorted(types)))
    return out

BP = bp_table(PLC)

ib = B['infobox']; links = B['infobox_links']; res = B['link_resolve']
txt = TEXTB['text_res']; tres = TEXTB['text_resolve']


def pick_link(titles, resolver):
    """first linked place that has coordinates; returns (qid, coarse) or None"""
    for t in titles:
        rr = resolver(t)
        if rr and rr.get('q') in BP and BP[rr['q']]['lon'] is not None:
            return rr['q']
    return None


def resolve(t):
    return res.get(t) or tres.get(t)


rows = []
for _, r in P.iterrows():
    rec = dict(person=r.person, name=r['name'], dob=r.dob[:10], sex={'Q6581097': 'male', 'Q6581072': 'female'}.get(r.sex, 'other or unknown' if r.sex else ''),
               n_p19=len(r.bps), bp='', bp_label='', bp_lon=None, bp_lat=None, bp_cty='', bp_source='', bp_precision='')
    q = src = None
    p19 = [x for x in r.bps if x.startswith('Q')]
    for x in p19:
        if x in BP and BP[x]['lon'] is not None:
            q, src = x, 'wikidata P19' + (' (coordinates of the containing place)' if BP[x]['how'] == 'parent' else '')
            break
    if q is None and not p19:
        q = pick_link(links.get(r.person, []) or [], resolve)
        if q:
            src = 'English Wikipedia infobox'
        else:
            t = txt.get(r.person)
            if t:
                q = pick_link([t.get('first') or t['link']], resolve)
                if q:
                    src = 'English Wikipedia article text'
    if q is None:
        rec['bp_source'] = ('wikidata P19 without coordinates' if p19 else 'wikidata P19 unknown value' if r.bps else 'none')
    else:
        b = BP[q]
        rec.update(bp=q, bp_label=b['label'], bp_cty=b['cty'], bp_source=src, bp_precision='coarse' if b['coarse'] else 'place')
        if not b['coarse']:
            rec.update(bp_lon=b['lon'], bp_lat=b['lat'])
        else:
            rec['bp_coarse_lon'], rec['bp_coarse_lat'] = b['lon'], b['lat']
    rows.append(rec)
people = pd.DataFrame(rows)
print(people.bp_source.value_counts()); print(people.bp_precision.value_counts())

# ---------- seat points ----------
pl = pd.read_csv(PLACES)
pl['q'] = pl['wikidata'].str.replace('wd:', '', regex=False)
seat = {r.q: (r.lon, r.lat, r.nation, r.place_source, r.label) for r in pl.itertuples()}
dist['dL'] = dist['dL'].map(lab)
for q, g in dist.groupby('d'):
    if q not in seat:
        c = [point(x) for x in g['coord'] if x]
        seat[q] = (c[0][0], c[0][1], '', 'wikidata P625 (not in sister file)', g['dL'].iloc[0]) if c else (None, None, '', 'none', g['dL'].iloc[0])

# ---------- geography: nations, counties ----------
nat = json.load(open(NATIONS)); cty = json.load(open(COUNTIES))
NAT = [(f['properties'].get('name') or f['properties'].get('nation'), prep(shape(f['geometry'])), shape(f['geometry'])) for f in nat['features']]
CTY = [(f['properties']['county'], f['properties']['nation'], prep(shape(f['geometry'])), shape(f['geometry'])) for f in cty['features']]
print('nation names', [n[0] for n in NAT])
HOME_CTY = {'Q145', 'Q27', 'Q174193', 'Q161885', 'Q179876', 'Q215530', 'Q9676', 'Q785', 'Q25230', 'Q22', 'Q21', 'Q25', 'Q26', 'Q3405693', 'Q1140026'}
CROWN = {'Q9676': 'Isle of Man', 'Q785': 'Jersey', 'Q25230': 'Guernsey', 'Q3405693': 'Sark', 'Q1140026': 'Alderney'}


def locate(lon, lat, ctys='', tol=0.12):
    """nation and county of a point; nearest polygon within 8 km for coastal points."""
    if lon is None or (isinstance(lon, float) and math.isnan(lon)):
        return '', ''
    p = Point(lon, lat)
    n = next((nm for nm, pp, g in NAT if pp.contains(p)), '')
    c = next((nm for nm, nn, pp, g in CTY if pp.contains(p)), '')
    if not n:
        cs = set(ctys.split('|')) if ctys else set()
        for q, nm in CROWN.items():
            if q in cs:
                return 'Crown Dependencies', ''
        if (-2.8 < lon < -2.0 and 49.1 < lat < 49.8) or (-4.9 < lon < -4.25 and 54.0 < lat < 54.45):
            return 'Crown Dependencies', ''  # Channel Islands, Isle of Man
        d, nm = min((g.distance(p), nm) for nm, pp, g in NAT)
        if d < tol:
            n = nm
    if n and n != 'Ireland' and not c:
        d, nm = min((g.distance(p), nm) for nm, nn, pp, g in CTY)
        if d < tol:
            c = nm
    if n == 'Ireland':
        c = ''
    return n, c


people[['bp_nation', 'bp_county']] = people.apply(lambda r: pd.Series(locate(r.bp_lon, r.bp_lat, r.bp_cty)), axis=1)
people['abroad'] = np.where(people.bp_lon.isna(), np.nan, (people.bp_nation == '').astype(float))
people.to_csv(WORK + 'people.csv', index=False)

# ---------- party family from the sister project's election results (read only) ----------
sis = '/home/claude/hist/elections-since-1832/data/'
con = pd.read_csv(sis + 'contests.csv', dtype=str)
cand = pd.read_csv(sis + 'candidates.csv', dtype=str)
cand = cand[cand.elected == 'True'].merge(con[['election', 'constituency', 'wikidata']], on=['election', 'constituency'], how='left')
cand['d'] = cand['wikidata'].str.replace('wd:', '', regex=False)
import unicodedata
def nrm(s):
    return re.sub(r'[^a-z ]', ' ', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()).split()
def sur_p(c):  # "Surname, Forename"
    w = nrm(str(c).split(',')[0]); return w[-1] if w else ''
cand['sur'] = cand['candidate'].map(sur_p)
WIN = collections.defaultdict(list)
for r in cand.itertuples():
    WIN[(r.election, r.d)].append((r.sur, r.family, r.party))
grpL = dict(zip(groups['g'], groups['gL'].map(lab)))
GRP_FAM = {'Conservative Party': 'CON', 'Labour Party': 'LAB', 'Liberal Party': 'LIB', 'Liberal Democrats': 'LIB',
           'Scottish National Party': 'SNP', 'Plaid Cymru': 'PC', 'Reform UK': 'REF', 'Green Party of England and Wales': 'GRN',
           'Sinn Féin': 'SF', 'Democratic Unionist Party': 'ULS', 'Ulster Unionist Party': 'ULS', 'Social Democratic and Labour Party': 'IRN',
           'Whigs': 'LIB', 'Tories': 'CON', 'Liberal Unionist Party': 'LU', 'Irish Parliamentary Party': 'IRN', 'Peelite': 'PEEL'}

name = dict(zip(people.person, people['name']))
fam, fsrc, plabel = [], [], []
for r in gen.itertuples():
    w = WIN.get((r.election, r.d), [])
    nm = name.get(r.person, '') or ''
    toks = nrm(re.sub(r'\(.*?\)', '', nm))
    hit = [x for x in w if x[0] and x[0] in toks]
    if len(w) == 1:
        fam.append(w[0][1]); fsrc.append('seat winner'); plabel.append(w[0][2])
    elif len(hit) >= 1 and len({h[1] for h in hit}) == 1:
        fam.append(hit[0][1]); fsrc.append('winner surname match'); plabel.append(hit[0][2])
    else:
        g = grpL.get(r.grp, '')
        fam.append(GRP_FAM.get(g, 'OTH' if g else '')); fsrc.append('wikidata P4100' if g else 'unknown'); plabel.append(g)
gen['family'] = fam; gen['family_source'] = fsrc; gen['party_label'] = plabel
print(gen.family_source.value_counts())

# ---------- assemble ----------
def hav(lon1, lat1, lon2, lat2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

pp = people.set_index('person')
out = []
seat_loc = {}
for r in gen.itertuples():
    s = seat.get(r.d, (None, None, '', 'none', ''))
    if r.d not in seat_loc:
        seat_loc[r.d] = locate(s[0], s[1], tol=0.6) if s[0] is not None else ('', '')
    sn, sc = seat_loc[r.d]
    p = pp.loc[r.person]
    rec = dict(election=r.election, year=int(r.election[-4:]), person=r.person, name=p['name'], sex=p.sex,
               seat=r.d, seat_label=s[4], seat_lon=s[0], seat_lat=s[1], seat_nation=s[2] or sn, seat_county=sc,
               seat_point_source=s[3], family=r.family, family_source=r.family_source, party_label=r.party_label,
               bp=p.bp, bp_label=p.bp_label, bp_lon=p.bp_lon, bp_lat=p.bp_lat, bp_nation=p.bp_nation,
               bp_county=p.bp_county, bp_source=p.bp_source)
    known = p.bp_lon is not None and not (isinstance(p.bp_lon, float) and math.isnan(p.bp_lon))
    rec['bp_known'] = int(known)
    if known and s[0] is not None:
        rec['dist_km'] = round(hav(s[0], s[1], p.bp_lon, p.bp_lat), 1)
        rec['born_abroad'] = int(p.bp_nation == '')
        rec['born_ireland'] = int(p.bp_nation == 'Ireland')
        rec['born_london'] = int(p.bp_county == 'Greater London')
        rec['same_nation'] = int(p.bp_nation == rec['seat_nation'])
        rec['same_county'] = (int(p.bp_county == sc) if sc else None)
    out.append(rec)
T = pd.DataFrame(out)
T['ei'] = T['election'].map(ELECTIONS.index)
T = T.sort_values(['ei', 'seat_label', 'name']).drop(columns='ei')
T.to_csv(WORK + 'mp_elections_full.csv.gz', index=False)
print(len(T), 'rows', T.person.nunique(), 'people')
print(T.groupby('year').bp_known.mean().round(2).to_dict())
print('seat points missing', T.seat_lon.isna().sum(), 'seat county blank', (T.seat_county == '').sum())
print(T.seat_nation.value_counts().to_dict())
print(T[T.bp_known == 1].bp_nation.value_counts().to_dict())
