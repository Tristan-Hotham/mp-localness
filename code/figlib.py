"""Shared matplotlib helpers for the header, paper and blog figures and the collage."""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..'))
FD = os.environ.get('FONT_DIR', '/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts')
for f in ['FrauncesVar.ttf', 'IBMPlexMono-Regular.ttf', 'IBMPlexMono-Medium.ttf', 'SourceSerif4-Regular.ttf', 'SourceSerif4-Semibold.ttf', 'SourceSerif4-It.ttf']:
    if os.path.exists(os.path.join(FD, f)):
        fm.fontManager.addfont(os.path.join(FD, f))
DISP = fm.FontProperties(fname=os.path.join(FD, 'FrauncesVar.ttf'), weight=900) if os.path.exists(os.path.join(FD, 'FrauncesVar.ttf')) else None
SER, MONO = 'Source Serif 4', 'IBM Plex Mono'
BG, FG, MUT, RULE, LAND, HOT, GOLD, ABR, NONE = '#F4F0E6', '#1D1C19', '#67625A', '#D8D1C2', '#E6E0D1', '#0F6B5C', '#B5702A', '#6A4A9C', '#ADA799'
BCOL = ['#0B5E50', '#2F8F74', '#8CBF84', '#E3C66E', '#DE8B3E', '#A9432A']
BANDS = [10, 25, 50, 100, 200, 1e9]
BLAB = ['under 10 km', '10 to 25 km', '25 to 50 km', '50 to 100 km', '100 to 200 km', '200 km or more']
FAMC = {'CON': '#0A60A8', 'LAB': '#D0262D', 'LIB': '#F2A31B', 'SNP': '#C9A800', 'IRN': '#2E8B3E'}
FAMN = {'CON': 'Conservative', 'LAB': 'Labour', 'LIB': 'Liberal, Whig, Lib Dem', 'SNP': 'SNP', 'IRN': 'Irish nationalist'}
plt.rcParams.update({'font.family': SER, 'font.size': 13, 'axes.edgecolor': MUT, 'axes.labelcolor': FG, 'xtick.color': MUT, 'ytick.color': MUT,
                     'axes.spines.top': False, 'axes.spines.right': False, 'savefig.facecolor': BG, 'figure.facecolor': BG, 'axes.facecolor': BG})
R = json.load(open(os.path.join(ROOT, 'data', 'results.json')))
D = json.load(open(os.path.join(ROOT, 'data', 'page', 'mps.json')))
NAT = json.load(open(os.path.join(ROOT, 'data', 'nations.geojson')))
K = math.cos(math.radians(54.5))


def band(km):
    for i, b in enumerate(BANDS):
        if km < b:
            return i
    return 5


def xy(lon, lat):
    return lon * K, lat


def land(ax, fc=LAND, ec=MUT, lw=0.4):
    for f in NAT['features']:
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for p in polys:
            a = np.array(p[0]); ax.fill(a[:, 0] * K, a[:, 1], fc=fc, ec=ec, lw=lw, zorder=1)


def mapax(ax, ext=(-10.6, 1.9, 49.85, 58.75)):
    ax.set_xlim(ext[0] * K, ext[1] * K); ax.set_ylim(ext[2], ext[3]); ax.set_aspect('equal'); ax.axis('off')


def election_rows(e):
    return D['E'][D['elections'].index(e)]['rows']


def lines_map(ax, e, lw=0.55, alpha=0.55, dot=9, abroad=True):
    """seat-to-birthplace lines and seat dots for one election, coloured by distance band"""
    segs, cols, pts, pcs = [], [], [], []
    for r in election_rows(e):
        s = D['seats'][r[0]]; p = D['people'][r[1]]
        sx, sy = xy(s[1], s[2])
        if p[2] is None:
            pts.append((sx, sy)); pcs.append(None); continue
        c = ABR if p[4] == 'A' else BCOL[band(r[3])]
        if p[4] != 'A' or abroad:
            segs.append([(sx, sy), xy(p[2], p[3])]); cols.append(c)
        pts.append((sx, sy)); pcs.append(c)
    order = np.argsort([-(BCOL.index(c) if c in BCOL else 6) for c in cols])
    from matplotlib.colors import to_rgba
    far = {BCOL[4], BCOL[5], ABR}
    rgba = [to_rgba(cols[i], alpha * (0.55 if cols[i] in far else 1.0)) for i in order]
    ax.add_collection(LineCollection([segs[i] for i in order], colors=rgba, linewidths=[lw * (0.8 if cols[i] in far else 1.6) for i in order], zorder=2))
    for (x, y), c in zip(pts, pcs):
        if c is None:
            ax.scatter([x], [y], s=dot * .8, facecolor='none', edgecolor=NONE, lw=.7, zorder=3)
    xs = [p for p, c in zip(pts, pcs) if c]; cs = [c for c in pcs if c]
    ax.scatter([p[0] for p in xs], [p[1] for p in xs], s=dot, c=cs, edgecolor=BG, lw=.3, zorder=4)
