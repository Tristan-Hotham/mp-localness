"""Fill code/page_template.html from data/results.json to make index.html.
{{path.to.value}} placeholders take values from results.json (plus the formatted helper values in
results['p']); /*R*/ gets the small summary the charts and the map use."""
import json, re, sys
sys.path.insert(0, '/home/claude/hist/mp-localness/code')
from common import *

R = json.load(open(OUT + 'results.json'))
BE = R['by_election']
E = [s['election'] for s in BE]
f = lambda n: f"{n:,}"
fam = {(s['family'], s['era']): s for s in R['by_family_era']}
p = dict(
    n_rows=f(R['n_rows']), n_people=f(R['n_people']),
    sc_flat=f"{round(R['long_flat']['same_county_min'])} to {round(R['long_flat']['same_county_max'])}%",
    sc_2024=R['h']['2024']['same_county'], cov_2024=R['h']['2024']['coverage'],
    med_2010=round(R['h']['2010']['median_km']), med_2024=round(R['h']['2024']['median_km']),
    lab97={k: v for k, v in R['by_family_since1997'][1].items()}, con97=R['by_family_since1997'][0],
    lib97=R['by_family_since1997'][2], snp97=R['by_family_since1997'][3],
    con8305=fam[('CON', '1983 to 2005')], con1019=fam[('CON', '2010 to 2019')],
    lab8305=fam[('LAB', '1983 to 2005')], lab1019=fam[('LAB', '2010 to 2019')], lab24=fam[('LAB', '2024')],
    reg={s['region']: s for s in R['by_region_since2010']},
    lon_min=min(s['london'] for s in BE if s['year'] >= 1992), lon_max=max(s['london'] for s in BE if s['year'] >= 1992),
    ab_americas=R['abroad_groups']['The Americas'], ab_aus=R['abroad_groups']['Australia and New Zealand'],
    ab_eu_early=R['abroad_groups_by_period']['first elected 1832 to 1910']['Europe'],
    ab_sa_early=R['abroad_groups_by_period']['first elected 1832 to 1910']['South Asia'],
    ab_eu_late=R['abroad_groups_by_period']['first elected 1983 to 2024']['Europe'],
    ab_sa_late=R['abroad_groups_by_period']['first elected 1983 to 2024']['South Asia'],
    cov_min9719=min(s['coverage'] for s in BE if 1997 <= s['year'] <= 2019), cov_max9719=max(s['coverage'] for s in BE if 1997 <= s['year'] <= 2019),
    fam_unknown=f(R['family_source'].get('unknown', 0)),
    src_w=f(R['n_people_point_by_source'].get('wikidata P19', 0)), src_i=f(R['n_people_point_by_source'].get('English Wikipedia infobox', 0)),
    src_t=f(R['n_people_point_by_source'].get('English Wikipedia article text', 0)),
)
R['p'] = p
json.dump(R, open(OUT + 'results.json', 'w'), indent=1, ensure_ascii=False)

UK = [[49.9, -10.4], [58.9, 1.8]]
h = R['h']
stories = [
    dict(t='1832', d=f"{h['1832']['same_county']}% born in the county", e='1832', b=UK, long=f"The first reformed Parliament. Of the MPs I can place ({h['1832']['coverage']}% of {h['1832']['n']}), {h['1832']['same_county']}% were born in their seat's county and {h['1832']['london']}% in London. Hollow dots are MPs whose birthplace is not known."),
    dict(t='1950', d='The middle of the long flat line', e='1950', mode='county', b=UK, long=f"In 1950, {h['1950']['same_county']}% of placed MPs were born in their seat's county, close to the 1832 figure. Green: same county; orange: another county."),
    dict(t='2005', d='Lines to birthplaces', e='2005', lines=True, b=UK, long=f"Lines join each MP's seat to where they were born. In 2005, {R['by_election'][E.index('2005')]['same_county']}% were born in the seat's county; many lines run to London and the big cities."),
    dict(t='2024', d=f"{h['2024']['same_county']}% born in the county", e='2024', mode='county', b=UK, long=f"In 2024, {h['2024']['same_county']}% of the MPs I can place were born in their seat's county and {h['2024']['local25']}% within 25 km. Only {h['2024']['coverage']}% of 2024 MPs are placed, so treat this one with care."),
    dict(t='North East', d=f"{p['reg']['North East']['same_county']}% local since 2010", e='2019', mode='county', b=[[54.4, -2.8], [55.5, -1.0]], long=f"Since 2010, {p['reg']['North East']['same_county']}% of North East MPs were born in their seat's county, the highest share of any English region."),
    dict(t='Home Counties', d=f"{p['reg']['East of England']['london']}% London-born (East)", e='2019', lines=True, b=[[51.2, -1.2], [52.6, 1.8]], long=f"Since 2010, {p['reg']['East of England']['london']}% of MPs for seats in the East of England were born in London, and {p['reg']['South East']['london']}% in the South East."),
    dict(t='Lines, 1886', d='The Victorian House', e='1886', lines=True, b=UK, long=f"Every placed MP of 1886 joined to their birthplace. Irish seats are included; the county measure leaves out seats in what is now the Republic of Ireland."),
]
small = dict(elections=E, years=[s['year'] + (0.5 if s['election'].startswith('December') or s['election'].startswith('October') else 0) for s in BE],
             byE=[{k: s[k] for k in ['n', 'known', 'coverage', 'median_km', 'local25', 'same_county', 'london', 'abroad']} for s in BE],
             bounds=[[R['county_bounds'][e]['low'], R['county_bounds'][e]['high']] for e in E],
             eraNew=R['by_era_new'], bands=R['bands'], bandLabels=R['bands_labels'], eras=[x['era'] for x in R['by_era']],
             famEra=R['by_family_era'], regions=R['by_region_since2010'], stories=stories)

T = open(ROOT + 'code/page_template.html').read()


def get(path):
    x = R
    for k in path.split('.'):
        x = x[int(k)] if isinstance(x, list) else x[k]
    return x


def fill(mo):
    path, _, fm = mo.group(1).partition('|')
    v = get(path.strip())
    if fm == 'int':
        return f"{int(round(v)):,}"
    return str(v)


T = re.sub(r'\{\{([^}]+)\}\}', fill, T)
T = T.replace('/*R*/', json.dumps(small, separators=(',', ':'), ensure_ascii=False))
open(ROOT + 'index.html', 'w').write(T)
print('index.html', len(T))
