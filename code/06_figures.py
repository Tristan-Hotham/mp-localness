"""header.png, paper figures (release/paper/fig_*.png) and blog figures (release/blog/b_*.png)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import *

PAPER = os.path.join(ROOT, 'release', 'paper'); BLOG = os.path.join(ROOT, 'release', 'blog')
os.makedirs(PAPER, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
BE = R['by_election']; YR = [s['year'] + (0.5 if s['election'][:3] in ('Dec', 'Oct') else 0) for s in BE]
E = [s['election'] for s in BE]


# ---------- header ----------
def header():
    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.text(.045, .79, 'Born', fontproperties=DISP, size=70, color=FG, va='bottom')
    fig.text(.045, .63, 'and bred?', fontproperties=DISP, size=70, color=HOT, va='bottom')
    fig.text(.047, .52, 'How local are MPs? Where MPs were born,\nset against the seats they won, 1832 to 2024', family=SER, size=18, color=FG, va='top', linespacing=1.35)
    fig.text(.047, .30, f"{R['p']['sc_flat']} born in the seat's county, 1832 to 2005", family=MONO, size=13, color=MUT)
    fig.text(.047, .25, f"{R['h']['2024']['same_county']}% in 2024", family=MONO, size=13, color=HOT)
    fig.text(.047, .085, 'maps.tristanhotham.com/mp-localness', family=MONO, size=12, color=MUT)
    ax = fig.add_axes([.55, .02, .43, .96]); land(ax, ec='none'); lines_map(ax, '2024', lw=.5, alpha=.5, dot=7, abroad=False); mapax(ax)
    ax.text(.04, .93, '2024', transform=ax.transAxes, fontproperties=DISP, size=26, color=FG)
    fig.savefig(os.path.join(ROOT, 'header.png'), dpi=100)
    plt.close(fig)


# ---------- charts (shared by paper and blog) ----------
def long_view(ax, big=False):
    lo = [R['county_bounds'][e]['low'] for e in E]; hi = [R['county_bounds'][e]['high'] for e in E]
    ax.fill_between(YR, lo, hi, color=HOT, alpha=.13, lw=0, label='possible range of the county share')
    ax.plot(YR, [s['local25'] for s in BE], color=GOLD, lw=2, ls=(0, (4, 3)), label='born within 25 km')
    ax.plot(YR, [s['same_county'] for s in BE], color=HOT, lw=2.8, marker='o', ms=3.5, label="born in the seat's county")
    ax.set_ylim(0, 80); ax.set_xlim(1828, 2028); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.grid(axis='y', color=RULE, lw=.8); ax.set_axisbelow(True)
    ax.legend(loc='upper center', frameon=False, ncol=3 if big else 1, fontsize=12 if big else 10)


def coverage(ax):
    ax.bar(YR, [s['coverage'] for s in BE], width=2.2, color=HOT, alpha=.85)
    ax.set_ylim(0, 100); ax.set_xlim(1828, 2028); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.grid(axis='y', color=RULE, lw=.8); ax.set_axisbelow(True)


def new_intake(ax, fs=12):
    rows = R['by_era_new']; y = np.arange(len(rows))[::-1]
    ax.barh(y, [s['local25'] for s in rows], color=[HOT if i >= 5 else NONE for i in range(len(rows))], height=.62)
    for yy, s in zip(y, rows):
        ax.text(s['local25'] + 1, yy, f"{s['local25']}%", va='center', family=MONO, size=fs, color=FG)
        ax.text(66, yy, f"{s['coverage']}% placed", va='center', ha='right', family=MONO, size=fs - 2, color=MUT)
    ax.set_yticks(y); ax.set_yticklabels([s['era'] for s in rows], family=MONO, size=fs)
    ax.set_xlim(0, 66); ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0)


def party(ax, fs=11):
    eras = [x['era'] for x in R['by_era']]; X = np.arange(len(eras))
    fe = {(s['family'], s['era']): s for s in R['by_family_era']}
    mk = {'CON': 'o', 'LAB': 's', 'LIB': '^', 'SNP': 'D', 'IRN': 'v'}
    for f in ['CON', 'LIB', 'LAB', 'SNP', 'IRN']:
        v = [fe[(f, e)]['same_county'] if (f, e) in fe and fe[(f, e)]['same_county'] is not None else np.nan for e in eras]
        ax.plot(X, v, color=FAMC[f], lw=2.4, marker=mk[f], ms=6, label=FAMN[f])
    ax.set_xticks(X); ax.set_xticklabels([e.replace(' to ', '\nto ') for e in eras], family=MONO, size=fs - 1)
    ax.set_ylim(0, 60); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.grid(axis='y', color=RULE, lw=.8); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=fs, ncol=3, loc='upper left')


def regions(ax, fs=12):
    rows = sorted(R['by_region_since2010'], key=lambda s: s['same_county']); y = np.arange(len(rows))
    ax.barh(y, [s['same_county'] for s in rows], color=HOT, height=.6, label="born in the seat's county")
    ax.scatter([s['london'] for s in rows], y, marker='|', s=260, lw=3, color=GOLD, zorder=3, label='born in London')
    for yy, s in zip(y, rows):
        ax.text(max(s['same_county'], s['london']) + 1.5, yy, f"{s['same_county']}%", va='center', family=MONO, size=fs - 1)
    ax.set_yticks(y); ax.set_yticklabels([s['region'] for s in rows], size=fs)
    ax.set_xlim(0, 108); ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0); ax.legend(frameon=False, loc='lower right', fontsize=fs - 1)


def london(ax, fs=11):
    ax.plot(YR, [s['london'] for s in BE], color=GOLD, lw=2.4, label='born in London')
    ax.plot(YR, [s['abroad'] for s in BE], color=ABR, lw=2.4, ls=(0, (5, 2)), label='born abroad')
    ax.set_ylim(0, 40); ax.set_xlim(1828, 2028); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.grid(axis='y', color=RULE, lw=.8); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=fs)


def two_maps(fig, eras=('1886', '2024'), fs=22):
    for k, e in enumerate(eras):
        ax = fig.add_axes([k * .5, .06, .5, .92]); land(ax, ec='none'); lines_map(ax, e, lw=.55, alpha=.6, dot=fs * .6); mapax(ax)
        s = R['by_election'][E.index(e)]
        ax.text(.05, .94, e, transform=ax.transAxes, fontproperties=DISP, size=fs, color=FG)
        ax.text(.05, .885, f"same county {s['same_county']}%\nmedian {round(s['median_km'])} km", transform=ax.transAxes, family=MONO, size=fs * .5, color=MUT, va='top')
    hs = [plt.Line2D([], [], color=c, lw=3) for c in BCOL] + [plt.Line2D([], [], color=ABR, lw=3), plt.Line2D([], [], marker='o', ls='', mfc='none', mec=NONE)]
    fig.legend(hs, BLAB + ['born abroad', 'birthplace unknown'], loc='lower center', ncol=4, frameon=False, fontsize=fs * .45, prop={'family': MONO, 'size': fs * .45})


def save(fig, path, dpi):
    fig.savefig(path, dpi=dpi); plt.close(fig)


header()
# paper (print, 6.3 in wide)
fig = plt.figure(figsize=(7, 5.4)); two_maps(fig, fs=15); save(fig, os.path.join(PAPER, 'fig_maps.png'), 220)
fig, ax = plt.subplots(figsize=(7, 3.6)); long_view(ax); ax.set_ylabel('share of MPs placed'); fig.tight_layout(); save(fig, os.path.join(PAPER, 'fig_long.png'), 220)
fig, ax = plt.subplots(figsize=(7, 2.4)); coverage(ax); ax.set_ylabel('placed'); fig.tight_layout(); save(fig, os.path.join(PAPER, 'fig_coverage.png'), 220)
fig, ax = plt.subplots(figsize=(7, 3.3)); new_intake(ax, 10); ax.set_xlabel('new MPs born within 25 km of their first seat'); fig.tight_layout(); save(fig, os.path.join(PAPER, 'fig_new.png'), 220)
fig, ax = plt.subplots(figsize=(7, 3.6)); party(ax, 9); ax.set_ylabel("born in seat's county"); fig.tight_layout(); save(fig, os.path.join(PAPER, 'fig_party.png'), 220)
fig, ax = plt.subplots(figsize=(7, 4.0)); regions(ax, 10); fig.tight_layout(); save(fig, os.path.join(PAPER, 'fig_regions.png'), 220)
fig, ax = plt.subplots(figsize=(7, 2.8)); london(ax, 9); fig.tight_layout(); save(fig, os.path.join(PAPER, 'fig_london.png'), 220)
# blog (1520 px wide)
fig = plt.figure(figsize=(15.2, 11.2)); two_maps(fig, fs=34); save(fig, os.path.join(BLOG, 'b_lines_map.png'), 100)
fig, ax = plt.subplots(figsize=(15.2, 7)); long_view(ax, True); ax.tick_params(labelsize=14); fig.tight_layout(); save(fig, os.path.join(BLOG, 'b_long_view.png'), 100)
fig, ax = plt.subplots(figsize=(15.2, 6.4)); new_intake(ax, 16); ax.tick_params(axis='x', labelsize=14); fig.tight_layout(); save(fig, os.path.join(BLOG, 'b_new_intake.png'), 100)
fig, ax = plt.subplots(figsize=(15.2, 7.2)); party(ax, 15); ax.tick_params(axis='y', labelsize=14); fig.tight_layout(); save(fig, os.path.join(BLOG, 'b_parties.png'), 100)
fig, ax = plt.subplots(figsize=(15.2, 8.4)); regions(ax, 16); ax.tick_params(axis='x', labelsize=14); fig.tight_layout(); save(fig, os.path.join(BLOG, 'b_regions.png'), 100)
fig, ax = plt.subplots(figsize=(15.2, 4.8)); coverage(ax); ax.tick_params(labelsize=14); fig.tight_layout(); save(fig, os.path.join(BLOG, 'b_coverage.png'), 100)
print('ok')
