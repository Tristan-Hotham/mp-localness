"""r/dataisbeautiful collage: born_and_bred.png (2400 by 3000). Run from anywhere."""
import os, sys
RHERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(RHERE, "..", "code"))
from figlib import *

BGC = '#EEF2EA'  # pale sage
plt.rcParams.update({'savefig.facecolor': BGC, 'figure.facecolor': BGC, 'axes.facecolor': BGC})
h = R['h']; BE = R['by_election']; CB = R['county_bounds']; new = R['by_era_new']
YR = [s['year'] + (0.5 if s['election'][:3] in ('Dec', 'Oct') else 0) for s in BE]
E = [s['election'] for s in BE]
RUST = '#A9432A'

fig = plt.figure(figsize=(12, 15), dpi=200)
fig.text(.045, .968, 'Born and bred?', fontproperties=DISP, fontsize=60, color=FG, va='top')
fig.text(.047, .905, f"Where {R['n_people']:,} MPs were born, and how far that is from the seats they won. Every MP returned\nat {R['n_elections']} UK general elections, 1832 to 2024; each line joins a seat to its MP's birthplace.",
         family=SER, fontsize=16, color=FG, va='top', linespacing=1.35)

# hero: two line maps
for k, e in enumerate(['1886', '2024']):
    ax = fig.add_axes([.01 + k * .49, .455, .49, .40]); land(ax, fc='#DCE3D6', ec='none')
    lines_map(ax, e, lw=.7, alpha=.65, dot=10); mapax(ax, (-10.6, 1.9, 49.85, 58.9))
    s = BE[E.index(e)]
    ax.text(.04, .965, e, transform=ax.transAxes, fontproperties=DISP, fontsize=40, color=FG, va='top')
    ax.text(.045, .85, f"born in the seat's county: {s['same_county']}%\nmedian distance: {round(s['median_km'])} km",
            transform=ax.transAxes, family=MONO, fontsize=12.5, color=FG, va='top', linespacing=1.4, zorder=6,
            bbox=dict(boxstyle='round,pad=0.25', fc=BGC, ec='none', alpha=.85))
hs = [plt.Line2D([], [], color=c, lw=4) for c in BCOL] + [plt.Line2D([], [], color=ABR, lw=4), plt.Line2D([], [], marker='o', ls='', mfc='none', mec=NONE, ms=8)]
fig.legend(hs, BLAB + ['born abroad', 'birthplace not known'], loc='center', bbox_to_anchor=(.5, .452), ncol=4, frameon=False,
           prop={'family': MONO, 'size': 11.5}, handlelength=1.6, columnspacing=1.4, labelcolor=FG)

# headline numbers
nums = [(f"{round(R['long_flat']['same_county_min'])} to {round(R['long_flat']['same_county_max'])}%", "of MPs born in their seat's\ncounty at every election,\n1832 to 2005", HOT),
        (f"{h['2024']['same_county']}%", "in 2024, after rising\nat every election\nsince 2010", HOT),
        (f"{round(h['2024']['median_km'])} km", f"median distance from\nbirthplace to seat in 2024\n({round(h['2010']['median_km'])} km in 2010)", RUST),
        (f"{new[5]['local25']}%", f"of new MPs 2010 to 2019\nborn within 25 km of their\nseat ({new[4]['local25']}% for 1983 to 2005)", RUST)]
for i, (big, small, c) in enumerate(nums):
    x = [.045, .29, .52, .735][i]
    fig.text(x, .412, big, fontproperties=DISP, fontsize=33, color=c, va='top')
    fig.text(x, .368, small, family=SER, fontsize=13, color=FG, va='top', linespacing=1.3)

# long view chart
ax = fig.add_axes([.085, .128, .53, .132])
lo = [CB[e]['low'] for e in E]; hi = [CB[e]['high'] for e in E]
ax.fill_between(YR, lo, hi, color=HOT, alpha=.14, lw=0)
ax.plot(YR, [s['same_county'] for s in BE], color=HOT, lw=3, marker='o', ms=3.5)
ax.set_ylim(0, 80); ax.set_xlim(1828, 2028); ax.set_yticks([0, 20, 40, 60, 80])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%')); ax.tick_params(labelsize=11.5)
for t in ax.get_xticklabels() + ax.get_yticklabels():
    t.set_family(MONO)
ax.grid(axis='y', color='#CBD3C4', lw=.8); ax.set_axisbelow(True); ax.set_facecolor(BGC)
fig.text(.085, .298, "MPs born in their seat's county, every election", family=SER, fontsize=15, color=FG, fontweight='bold', va='top')
fig.text(.085, .279, 'Band: possible range given MPs whose birthplace is not known', family=MONO, fontsize=10.5, color=MUT, va='top')

# regions since 2010
ax = fig.add_axes([.80, .118, .17, .132])
rows = sorted([r for r in R['by_region_since2010'] if r['region'] != 'Northern Ireland'], key=lambda s: s['same_county'])
y = np.arange(len(rows))
ax.barh(y, [r['same_county'] for r in rows], color=HOT, height=.62)
for yy, r in zip(y, rows):
    ax.text(r['same_county'] + 1.5, yy, f"{round(r['same_county'])}%", va='center', family=MONO, fontsize=10, color=FG)
ax.set_yticks(y); ax.set_yticklabels([r['region'].replace('Yorkshire and the Humber', 'Yorkshire') for r in rows], fontsize=10.5, family=SER)
ax.set_xlim(0, 70); ax.set_xticks([]); ax.spines['bottom'].set_visible(False); ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0)
fig.text(.66, .302, 'Born in the seat\'s county,\nGreat Britain, 2010 to 2024', family=SER, fontsize=15, color=FG, fontweight='bold', va='top', linespacing=1.2)

# footer
fig.add_artist(plt.Line2D([.045, .955], [.094, .094], color=FG, lw=1.2))
fig.text(.045, .086, f"Birthplace known for {h['1832']['coverage']}% of MPs in 1832, {R['p']['cov_min9719']}% to {R['p']['cov_max9719']}% from 1997 to 2019 and {h['2024']['coverage']}% in 2024;\nshares are of MPs whose birthplace is known. County: one modern county map for all years. Seats are points.", family=MONO, fontsize=9.5, color=MUT, va='top', linespacing=1.35)
fig.text(.045, .056, 'Sources: Wikidata (CC0); English Wikipedia (CC BY-SA 4.0); UK Parliament Members API and Commons Library results\n'
         '(Open Parliament Licence v3.0); ONS counties (OGL v3.0); seat points from "Who won here?" (doi:10.5281/zenodo.23761425).',
         family=MONO, fontsize=9.5, color=MUT, va='top', linespacing=1.35)
fig.text(.045, .006, 'Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/mp-localness', family=MONO, fontsize=10.5, color=FG, va='bottom')
fig.savefig(os.path.join(RHERE, "born_and_bred.png"), dpi=200)
print('ok')
