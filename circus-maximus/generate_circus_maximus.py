"""
Travis Scott – Circus Maximus Tour (UTOPIA) – LEGO MOC Generator
Arena-lange Buehne als schwarze Fels-Spalte durch die Halle (in-the-round), Plattformen und Boegen,
ovaler 360-Grad-Videoring, fliegende Koepfe, PA-Haenge, Traversen-Raster. Massstab: 2 Baseplates 32x32.
Pipeline: Hoehenfeld -> Schale + Stuetz-Propagation -> Slopes an Stufenkanten -> Packing -> Checks -> MPD/BOM/XML
"""
import math, random, os, sys
from collections import defaultdict, Counter

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
NAME = "circus_maximus_stage"
random.seed(7)

LDU, BH, PH = 20, 24, 8
ROT = {0: "1 0 0 0 1 0 0 0 1", 90: "0 0 -1 0 1 0 1 0 0",
       180: "-1 0 0 0 1 0 0 0 -1", 270: "0 0 1 0 1 0 -1 0 0"}
RM = {k: [list(map(float, v.split()[i:i + 3])) for i in (0, 3, 6)] for k, v in ROT.items()}

# ---------------- Farben ----------------
BLACK, WHITE, BLUE, GREEN, RED, YELLOW, TAN, DTAN = 0, 15, 1, 2, 4, 14, 19, 28
LBG, DBG, TCLEAR, TYELLOW, MBLUE, DKRED = 71, 72, 47, 46, 73, 320
COLORS = {0: ("Black", 11), 15: ("White", 1), 1: ("Blue", 7), 2: ("Green", 6), 4: ("Red", 5),
          14: ("Yellow", 3), 19: ("Tan", 2), 28: ("Dark Tan", 69), 71: ("Light Bluish Gray", 86),
          72: ("Dark Bluish Gray", 85), 47: ("Trans-Clear", 12), 46: ("Trans-Yellow", 19),
          73: ("Medium Blue", 42), 320: ("Dark Red", 59), 70: ("Reddish Brown", 88),
          308: ("Dark Brown", 120), 272: ("Dark Blue", 63), 288: ("Dark Green", 80),
          148: ("Pearl Dark Gray", 77), 179: ("Flat Silver", 95)}

# ---------------- Teile ----------------
BRICK = {(1, 1): "3005", (1, 2): "3004", (1, 3): "3622", (1, 4): "3010", (1, 6): "3009", (1, 8): "3008",
         (2, 2): "3003", (2, 3): "3002", (2, 4): "3001", (2, 6): "2456", (2, 8): "3007"}
BRICK_CORE = {**BRICK, (1, 10): "6111", (1, 12): "6112", (2, 10): "3006"}
BRICK_TRANS = {(1, 1): "3005", (1, 2): "3065", (1, 4): "3066"}
PLATE = {(1, 1): "3024", (1, 2): "3023", (1, 3): "3623", (1, 4): "3710", (1, 6): "3666", (1, 8): "3460",
         (1, 10): "4477", (1, 12): "60479", (2, 2): "3022", (2, 3): "3021", (2, 4): "3020", (2, 6): "3795",
         (2, 8): "3034", (2, 10): "3832", (2, 12): "2445", (2, 16): "4282", (4, 4): "3031", (4, 6): "3032",
         (4, 8): "3035", (4, 10): "3030", (4, 12): "3029", (6, 6): "3958", (6, 8): "3036", (6, 10): "3033",
         (6, 12): "3028", (6, 14): "3456", (6, 16): "3027", (8, 8): "41539", (8, 16): "92438",
         (16, 16): "91405"}
TILE = {(1, 1): "3070b", (1, 2): "3069b", (1, 4): "2431", (1, 6): "6636", (1, 8): "4162",
        (2, 2): "3068b", (2, 4): "87079"}
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "6141": "4073", "3815c01": "970c00", "63142": "x127c30pb01"}
NAME_OVERRIDE = {"63142": "String with End Studs 30L overall (63142 / 14225)"}


class Part:
    __slots__ = ("sub", "name", "color", "x", "y", "z", "rot", "cells", "ytop", "ybot", "studs", "hang", "extra", "studcells")

    def __init__(s, sub, name, color, x, y, z, rot, cells, ytop, ybot, studs=True, hang=False, extra=None, studcells=None):
        s.sub, s.name, s.color, s.x, s.y, s.z, s.rot = sub, name, color, x, y, z, rot
        s.cells, s.ytop, s.ybot, s.studs, s.hang, s.extra = frozenset(cells), ytop, ybot, studs, hang, extra
        s.studcells = frozenset(cells if studcells is None else studcells) if studs else frozenset()

    def lines(s):
        if s.extra: return s.extra
        return [f"1 {s.color} {fmt(s.x)} {fmt(s.y)} {fmt(s.z)} {ROT[s.rot]} {s.name}.dat"]


def fmt(v):
    v = round(v, 3)
    return str(int(v)) if v == int(v) else str(v)


parts = []


def add(p):
    parts.append(p); return p


def ctr(i): return (i + 0.5) * LDU
def dist(c): return math.hypot(c[0] + 0.5, c[1] + 0.5)


N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
ALL = [(i, k) for i in range(-32, 32) for k in range(-32, 32)]
def disk(r): return {c for c in ALL if dist(c) <= r}
def boundary8(S): return {c for c in S if any((c[0] + a, c[1] + b) not in S for a, b in N8)}
def sector(c):
    x, z = c[0] + 0.5, c[1] + 0.5
    if abs(x) >= abs(z): return (1, 0) if x > 0 else (-1, 0)
    return (0, 1) if z > 0 else (0, -1)


# ---------------- Packing (Rechteck-Merge) ----------------
def pack(sub, cellcol, table, ytop_of_layer, height, parity, studs=True, radial=False, trans_table=None, tangential=False):
    """cellcol: {(i,k): color}. Liefert Parts. Rechtecke nur gleichfarbig.
    parity alterniert Vorzugsachse + Scanrichtung (Verzahnung). radial=True: Vorzugsachse je Sektor radial."""
    free = dict(cellcol)
    sizes = sorted(table.keys(), key=lambda s: -s[0] * s[1])
    order = sorted(free, key=(lambda c: (c[1], c[0])) if parity == 0 else (lambda c: (-c[0], -c[1])))
    sgn = 1 if parity == 0 else -1
    out = []
    for c in order:
        if c not in free: continue
        col = free[c]
        tab = trans_table if (trans_table and col == TCLEAR) else table
        if table is BRICK and col == BLACK: tab = BRICK_CORE
        best = None
        pref_x = (parity == 0)
        if radial: pref_x = sector(c)[0] != 0
        if tangential: pref_x = sector(c)[0] == 0
        for (w, l) in sorted(tab.keys(), key=lambda s: -s[0] * s[1]):
            for (xs, zs) in ((l, w), (w, l)) if l != w else ((l, w),):
                if (radial or tangential) and xs != zs and (xs > zs) != pref_x: continue
                cells = [(c[0] + sgn * a, c[1] + sgn * b) for a in range(xs) for b in range(zs)]
                if all(free.get(q) == col for q in cells):
                    score = xs * zs * 10 + (1 if (xs >= zs) == pref_x else 0)
                    if best is None or score > best[0]: best = (score, xs, zs, cells, (w, l))
        _, xs, zs, cells, key = best
        for q in cells: del free[q]
        cx = sum(ctr(q[0]) for q in cells) / len(cells)
        cz = sum(ctr(q[1]) for q in cells) / len(cells)
        rot = 0 if xs >= zs else 90
        name = tab[key]
        out.append(add(Part(sub, name, col, cx, ytop_of_layer, cz, rot, cells, ytop_of_layer, ytop_of_layer + height, studs)))
    return out


def bricks(sub, cellcol, g, parity=None, trans=True):
    y = -BH * (g + 1)
    return pack(sub, cellcol, BRICK, y, BH, g % 2 if parity is None else parity, trans_table=BRICK_TRANS if trans else None)


def plates(sub, cellcol, ytop, parity, table=PLATE, studs=True, radial=False, tangential=False):
    return pack(sub, cellcol, table, ytop, PH, parity, studs=studs, radial=radial, tangential=tangential)


def radial_runs(cells):
    """Zerlegt Zellen in radiale Reihen je Sektor (zusammenhaengende Laeufe, nach aussen sortiert)."""
    rows = defaultdict(list)
    for c in cells:
        sx, sz = sector(c)
        key = (sx, sz, c[1] if sx else c[0])
        rows[key].append(c)
    runs = []
    for (sx, sz, t), cs in rows.items():
        cs.sort(key=lambda c: abs(c[0]) if sx else abs(c[1]))
        cur = [cs[0]]
        for c in cs[1:]:
            if abs((c[0] - cur[-1][0]) + (c[1] - cur[-1][1])) == 1: cur.append(c)
            else: runs.append(cur); cur = [c]
        runs.append(cur)
    return runs


SIZES1 = sorted(k[1] for k in PLATE if k[0] == 1)
def split_run(L, sizes=None):
    sizes = sizes or SIZES1
    if L in sizes: return [L]
    for a in sorted(sizes, reverse=True):
        if (L - a) in sizes: return [a, L - a]
    out = []
    while L > 0:
        a = max(x for x in sizes if x <= L); out.append(a); L -= a
    return out


def place_runs(sub, runs, color, ytop, table=PLATE, height=PH, hang=False, studs=True):
    res = []
    sizes = sorted(k[1] for k in table if k[0] == 1)
    for run in runs:
        pos = 0
        for n in split_run(len(run), sizes):
            seg = run[pos:pos + n]; pos += n
            xs = {c[0] for c in seg}
            cx = sum(ctr(c[0]) for c in seg) / n; cz = sum(ctr(c[1]) for c in seg) / n
            rot = 0 if len(xs) >= len({c[1] for c in seg}) else 90
            res.append(add(Part(sub, table[(1, n)], color, cx, ytop, cz, rot, seg, ytop, ytop + height, studs, hang)))
    return res


def bond_layer(sub, cells, lower, ytop, color, max_len=6):
    """Plattenlage, die die Teile 'lower' (Lage darunter) sicher zu EINEM Stueck verbindet:
    Kruskal-artig - zuerst Platten, die die meisten noch getrennten Stuecke ueberbruecken,
    danach Rest auffuellen. Liefert (Teile, Anzahl Stuecke danach)."""
    owner = {c: k for k, p in enumerate(lower) for c in p.cells if c in cells}
    par = list(range(len(lower)))
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    free = set(cells)
    sizes = [(1, n) for n in (1, 2, 3, 4, 6) if n <= max_len] + [(2, 2), (2, 3), (2, 4)]
    cand = []
    for c in cells:
        for (w, l) in sizes:
            for (xs, zs) in {(l, w), (w, l)}:
                rect = tuple((c[0] + a, c[1] + b) for a in range(xs) for b in range(zs))
                if all(q in free for q in rect): cand.append(rect)
    placed = []
    while True:
        best = None
        for rect in cand:
            if not all(q in free for q in rect): continue
            comps = {find(owner[q]) for q in rect if q in owner}
            if len(comps) < 2: continue
            key = (len(comps), -len(rect))           # viele Stuecke verbinden, dabei moeglichst kleine Platte
            if best is None or key > best[0]: best = (key, rect, comps)
        if best is None: break
        _, rect, comps = best
        comps = list(comps)
        for k in comps[1:]: par[find(k)] = find(comps[0])
        free -= set(rect); placed.append(rect)
    res = []
    for rect in placed:
        xs = {q[0] for q in rect}; zs = {q[1] for q in rect}
        key = (min(len(xs), len(zs)), max(len(xs), len(zs)))
        cx = sum(ctr(q[0]) for q in rect) / len(rect); cz = sum(ctr(q[1]) for q in rect) / len(rect)
        res.append(add(Part(sub, PLATE[key], color, cx, ytop, cz, 0 if len(xs) >= len(zs) else 90, rect, ytop, ytop + PH)))
    res += plates(sub, {c: color for c in free}, ytop, 1, tangential=True)
    n_comp = len({find(k) for k in range(len(lower))})
    return res, n_comp



# =====================================================================================
#                          CIRCUS MAXIMUS (UTOPIA) – TRAVIS SCOTT
# =====================================================================================
# Koordinaten: Zellen x in [-32, 31] (Laengsachse der Arena), z in [-16, 15]. Die Buehne liegt als lange
# Fels-Spalte mitten im Innenraum (in-the-round, Publikum rundherum). Ueber ihr haengt ein ovaler
# 360-Grad-Videoring, dazwischen fliegende Koepfe; getragen von einem Traversen-Raster auf 6 Tuermen.
COLORS.update({36: ("Trans-Red", 17)})
# Farbkonzept nach den Fotos: grauer, verwitterter Stein (Dunkelgrau, Hellgrau im Licht, Schwarz in Spalten),
# schwarzer Buehnenboden, weisse Glotzaugen der Koepfe als hellster Punkt.
XMIN, XMAX, ZMIN, ZMAX = -32, 31, -16, 15
GRID = [(i, k) for i in range(XMIN, XMAX + 1) for k in range(ZMIN, ZMAX + 1)]
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ROT_OUT = {(1, 0): 90, (-1, 0): 270, (0, 1): 180, (0, -1): 0}    # Slope-Gefaelle (Standard: nach -z)


def vnoise(x, z, sc=3.0, seed=0):
    """glatte Werte-Rauschfunktion 0..1"""
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx
    b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


# ---------------- Hoehenfeld: gewundener Fels-Pfad ----------------
# Nach den Buehnen-Renderings: schmaler Weg, der sich durch die Halle windet, beidseitig Felswaende und
# Findlinge mit Gesichtern; an einem Ende ein hoher Felsblock mit eingemeisselten Gesichtern und Durchgang.
DECK = 2                                   # Laufweg (Steine)
PATH = [(-29.0, -2.0), (-13.0, -2.0), (-9.0, 1.0), (-4.0, -2.0), (1.0, 2.5), (6.0, -2.0), (15.0, 0.0), (28.0, 2.0)]
SX0, SX1 = -28, 27
BLOCK_X = (-28, -21)                       # hoher Felsblock
BLOCK_H = 12
WALK_HW = 1.6                              # halbe Wegbreite (4 Zellen)
BOULDERS = [(-10.0, 1), (-1.0, -1), (8.0, 1), (17.0, -1), (24.0, 1)]   # Findlings-Koepfe (x, Seite)


def zc(x):
    for (x0, z0), (x1, z1) in zip(PATH, PATH[1:]):
        if x0 <= x <= x1: return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return PATH[-1][1]


def in_block(x): return BLOCK_X[0] <= x < BLOCK_X[1] + 1


def half_width(x):
    if in_block(x): return 5.6
    w = 3.7 + 0.7 * math.sin(0.55 * x + 0.3) + 0.5 * math.sin(1.3 * x)
    return w * min(1.0, (SX1 + 1 - x) / 3.0) if x > SX1 - 2 else w


def boulder(x, z):
    """Findlinge: runde Kuppen am Wegrand"""
    h = 0.0
    for bx, side in BOULDERS:
        bz = zc(bx) + side * (WALK_HW + 2.0)
        r = math.hypot(x - bx, z - bz)
        if r < 2.4: h = max(h, DECK + 5.8 - r * 1.4)
    return h


def stage_f(p):
    """kontinuierliche Felshoehe (Steine); 0 = ausserhalb"""
    x, z = p
    if not (SX0 <= x <= SX1 + 1): return 0.0
    d = abs(z - zc(x)); W = half_width(x); b = boulder(x, z)
    if d <= WALK_HW: return float(DECK)
    if d > W: return b
    if in_block(x): return BLOCK_H + 1.4 * (vnoise(x, z, 2.0, 5) - 0.5)
    h = DECK + 1.3 + 2.4 * vnoise(x, z, 2.6, 3) + 0.9 * vnoise(x, z, 1.3, 4)
    return max(h, b)


# Ecktuerme + Mitte: je 1 Gittertraeger-Stapel (Rasterpunkt = Mitte 2x2)
TOWERS = [(-31, -15), (-31, 15), (31, -15), (31, 15), (0, -15), (0, 15)]
RESERVED = {(X + a, Z + b) for X, Z in TOWERS for a in (-1, 0) for b in (-1, 0)}
HF, MAT = {}, {}
for c in GRID:
    if c in RESERVED: continue
    p = (c[0] + 0.5, c[1] + 0.5)
    h = stage_f(p)
    if h <= 0.5: continue
    if abs(p[1] - zc(p[0])) <= WALK_HW and SX0 <= p[0] <= SX1 + 1: HF[c], MAT[c] = DECK, "weg"
    else: HF[c], MAT[c] = max(DECK + 1, int(math.floor(h + 0.5))), "fels"
for x in (SX0 - 1, SX1 + 1):                                      # Stufe zum Hallenboden an beiden Enden
    for z in range(ZMIN, ZMAX + 1):
        if abs(z + 0.5 - zc(x + 0.5)) <= WALK_HW: HF[(x, z)], MAT[(x, z)] = 1, "weg"
# Oberseite des Blocks flach (Performer-Plattform wie auf dem Stadionfoto)
PLAT_CELLS = {c for c in HF if MAT[c] == "fels" and in_block(c[0] + 0.5) and abs(c[1] + 0.5 - zc(c[0] + 0.5)) < 4.3}
for c in PLAT_CELLS: HF[c] = BLOCK_H
TUNNEL = sorted(c for c in HF if MAT[c] == "weg" and in_block(c[0] + 0.5))
GMAX = max(HF.values())
S = [{c for c, h in HF.items() if h > g} for g in range(GMAX + 1)]

# Rockwork-Ueberhaenge an der Aussenkante: oberste Randlage kragt stellenweise 1 Noppe aus (umgedrehter Slope)
LIPS, _used = [], set()
for c in sorted(HF):
    if MAT[c] != "fels" or HF[c] < 3 or c in PLAT_CELLS: continue
    if in_block(c[0] + 0.5) or boulder(c[0] + 0.5, c[1] + 0.5) > 0: continue       # Gesichter frei halten
    g = HF[c] - 1
    if c not in S[g - 1] or vnoise(c[0] + 0.5, c[1] + 0.5, 2.2, 9) < 0.55: continue
    for d in DIRS:
        o = (c[0] + d[0], c[1] + d[1])
        if o in HF or o in RESERVED or o in _used or not (XMIN <= o[0] <= XMAX and ZMIN <= o[1] <= ZMAX): continue
        if any((o[0] + a, o[1] + b) in HF and MAT[(o[0] + a, o[1] + b)] == "weg" for a, b in N8): continue
        LIPS.append((c, o, d, g)); _used.add(o); break
for (c, o, d, g) in LIPS:
    HF[o] = g + 1; MAT[o] = "fels"
    for gg in range(g, g + 1): S[gg].add(o)
LIP_OUT = {(o, g) for _, o, _, g in LIPS}
LIP_O = {o for _, o, _, _ in LIPS}


def grad_dirs(c):
    p = (c[0] + 0.5, c[1] + 0.5)
    g = [(stage_f((p[0] + d[0] * 0.7, p[1] + d[1] * 0.7)) - stage_f(p), d) for d in DIRS]
    g.sort()
    return [d for _, d in g]


# ---------------- Farben ----------------
SUN = (-0.4, 0.8, -0.45)
def rock_color(c, top=False, g=None):
    """grauer, verwitterter Stein: Dunkelgrau als Grundton, Hellgrau im Licht, Schwarz in Spalten"""
    p = (c[0] + 0.5, c[1] + 0.5)
    if top:
        return LBG if vnoise(p[0], p[1], 2.4, 1) > 0.6 else DBG
    gx = stage_f((p[0] + 0.5, p[1])) - stage_f((p[0] - 0.5, p[1])); gz = stage_f((p[0], p[1] + 0.5)) - stage_f((p[0], p[1] - 0.5))
    gx, gz = max(-2.0, min(2.0, gx)), max(-2.0, min(2.0, gz))    # senkrechte Waende nicht ins Schwarze kippen
    n = (-gx, 1.0, -gz); L = math.sqrt(sum(v * v for v in n))
    shade = sum(a * b for a, b in zip(n, SUN)) / L
    shade += 0.35 * (vnoise(p[0], p[1] + (g or 0) * 0.7, 1.8, 7) - 0.5)
    return LBG if shade > 0.55 else DBG if shade > -0.15 else BLACK


ROCK = ("fels",)
SLOPE_OK = ("fels",)
SNOT_LINKS = []

# ---------------- Schale, Decks und Stuetzen ----------------
def chebyshev_dist(Sg):
    dist = {}; frontier = [c for c in Sg if any((c[0] + a, c[1] + b) not in Sg for a, b in N8)]
    for c in frontier: dist[c] = 1
    k = 1
    while frontier:
        nxt = []
        for c in frontier:
            for a, b in N8:
                q = (c[0] + a, c[1] + b)
                if q in Sg and q not in dist: dist[q] = k + 1; nxt.append(q)
        frontier = nxt; k += 1
    return dist


T_SHELL = 2
solid, deck = [set() for _ in range(GMAX + 1)], [set() for _ in range(GMAX + 1)]
pillars = [set() for _ in range(GMAX + 1)]
for g in range(GMAX + 1):
    Sg = S[g]; Sa = S[g + 1] if g + 1 <= GMAX else set()
    dist = chebyshev_dist(Sg)
    exposed = Sg - Sa
    deck[g] = {c for c in exposed if dist[c] > T_SHELL + 1 and MAT[c] != "weg"}
    solid[g] = {c for c in Sg if dist[c] <= T_SHELL or c in exposed} - deck[g]
    for c in deck[g]:
        if c[0] % 4 == 0 and c[1] % 4 == 0:
            blk = {(c[0] + a, c[1] + b) for a in (0, 1) for b in (0, 1)}
            if blk <= deck[g]: pillars[g] |= blk
for g in range(GMAX, 0, -1):
    solid[g - 1] |= {c for c in (solid[g] | pillars[g]) if (c, g) not in LIP_OUT}
    deck[g - 1] -= solid[g - 1]

# ---------------- Durchgang durch den Block ----------------
# Je x ein Bogen 1x6x2 quer ueber den Weg (Lagen 6-7), darueber Steine bis zur Blockoberkante.
replaced = set()
ARCH_BOT = 6
ARCHES = []
for x in range(BLOCK_X[0], BLOCK_X[1] + 1):
    zs = [c[1] for c in TUNNEL if c[0] == x]
    z0, z1 = min(zs) - 1, max(zs) + 1
    assert z1 - z0 + 1 == 6, (x, zs)
    for z in (z0, z1):
        assert MAT.get((x, z)) == "fels" and HF[(x, z)] >= ARCH_BOT + 3, (x, z)
        replaced.add(((x, z), ARCH_BOT)); replaced.add(((x, z), ARCH_BOT + 1))
    ARCHES.append((x, z0, z1))
BRIDGE = {(x, z) for x, z0, z1 in ARCHES for z in range(z0 + 1, z1)}
PILLAR_CELLS = set()

# ---------------- Gesichter (SNOT) ----------------
# Augen: Headlight-Stein 4070, darauf eine runde Fliese 1x1 (98138) auf der Seitennoppe.
# Mund: Stein 1x2 mit Seitennoppen 11211, darauf Gitterfliese 2412b.
M_FRONT = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]                      # Fliese mit Oberseite nach -z


def mat_str(rot):
    R = RM[rot]
    M = [[sum(R[i][k] * M_FRONT[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return " ".join(fmt(M[i][j]) for i in range(3) for j in range(3))


EYES, MOUTHS = [], []                     # (Zelle, Lage, Richtung, Farbe) / ((Zelle, Zelle), Lage, Richtung)


LIP_CG = {(c, g - 1) for c, _, _, g in LIPS} | {(o, g) for _, o, _, g in LIPS}


def free_face(c, g, d):
    o = (c[0] + d[0], c[1] + d[1])
    return c in S[g] and (c, g) not in replaced and (c, g) not in LIP_CG and o not in S[g] and o not in RESERVED \
        and o not in LIP_O


def outer_cell(x, side):
    zs = [z for (xx, z) in HF if xx == x and MAT[(xx, z)] == "fels" and (xx, z) not in LIP_O
          and (z + 0.5 - zc(x + 0.5)) * side > 0]
    return (x, max(zs, key=lambda z: z * side)) if zs else None


# Gesichter an beiden Langseiten des Blocks
for side in (-1, 1):
    d = (0, side)
    eyes = [outer_cell(x, side) for x in (-26, -23)]
    mouth = [outer_cell(x, side) for x in (-25, -24)]
    if None in eyes + mouth or len({c[1] for c in eyes + mouth}) != 1: continue
    if all(free_face(c, 8, d) for c in eyes) and all(free_face(c, 5, d) for c in mouth):
        for c in eyes: EYES.append((c, 8, d, LBG)); replaced.add((c, 8))
        MOUTHS.append((tuple(mouth), 5, d)); replaced |= {(c, 5) for c in mouth}
# Findlinge: zwei Augen zur Hallenseite
for bx, side in BOULDERS:
    d = (0, side)
    cand = [outer_cell(x, side) for x in (int(math.floor(bx)) - 1, int(math.floor(bx)) + 1)]
    if None in cand: continue
    g = min(HF[c] for c in cand) - 2
    if g >= DECK + 1 and all(free_face(c, g, d) for c in cand):
        for c in cand: EYES.append((c, g, d, LBG)); replaced.add((c, g))

# ---------------- Slopes an Stufenkanten ----------------
STEP_PART = {1: "3040b", 2: "4286", 3: "60477"}
STEEP_PART = {2: "60481", 3: "4460b"}
covered, SLOPES = set(), []
for (c, o, d, g) in LIPS:
    replaced.add((c, g - 1)); covered.add((o, g - 1))
for g in range(0, GMAX + 1):
    for c in sorted(S[g]):
        if MAT[c] not in SLOPE_OK or (c, g) in replaced or c not in solid[g] or c in PLAT_CELLS \
                or c in PILLAR_CELLS: continue
        for d in grad_dirs(c):
            n = (c[0] + d[0], c[1] + d[1])
            if n in S[g]: continue
            below = S[g - 1] if g > 0 else set(GRID)
            if n not in below or (n, g) in covered or MAT.get(n) == "weg" or n in PILLAR_CELLS or n in LIP_O: continue
            if any((q, L) in replaced for q in (c, n) for L in range(g, g + 3)): continue
            run, q = [], n
            while q in below and q not in S[g] and (q, g) not in covered and len(run) < 3 and q not in RESERVED \
                    and MAT.get(q) != "weg" and q not in PILLAR_CELLS and q not in LIP_O and XMIN <= q[0] <= XMAX and ZMIN <= q[1] <= ZMAX:
                run.append(q); q = (q[0] + d[0], q[1] + d[1])
            if not run: continue
            if g == 0: run = run[:1]
            h = 1
            while h < 3 and g + h <= GMAX and c in S[g + h] and (c, g + h) not in replaced and c in solid[g + h]:
                h += 1
            if h >= 2: name, cells, layers = STEEP_PART[h], [c, n], range(g, g + h)
            else: name, cells, layers = STEP_PART[len(run)], [c] + run, [g]
            SLOPES.append((name, c, d, g, len(layers), cells))
            for L in layers:
                replaced.add((c, L))
                for q in cells[1:]: covered.add((q, L))
            break

# ---------------- Bauen: Lagen ----------------
def side_visible(c, g):
    return any((c[0] + a, c[1] + b) not in S[g] for a, b in DIRS)


def body_color(c, g):
    vis = side_visible(c, g) or c not in (S[g + 1] if g + 1 <= GMAX else set())
    if MAT[c] == "weg": return BLACK
    return rock_color(c, g=g) if vis else BLACK


def sub_of(c):
    return "03_laufweg" if MAT[c] == "weg" else "02_felsen"


for g in range(GMAX + 1):
    cells = {c for c in solid[g] if (c, g) not in replaced}
    bysub = defaultdict(dict)
    for c in cells: bysub[sub_of(c)][c] = body_color(c, g)
    for sb, cc in bysub.items(): bricks(sb, cc, g)
    if deck[g]:
        y0 = -BH * g
        dc = deck[g]
        l1 = plates("02_felsen", {c: BLACK for c in dc}, y0 - PH, 0)
        sup = solid[g - 1] if g > 0 else set(GRID)
        for p in l1:
            if not (p.cells & sup): p.hang = True
        bond_layer("02_felsen", dc, l1, y0 - 2 * PH, BLACK)
        plates("02_felsen", {c: BLACK for c in dc}, y0 - 3 * PH, 1)
for (c, o, d, g) in LIPS:
    y = -BH * g
    add(Part("02_felsen", "3665a", rock_color(c, g=g - 1), ctr(c[0]), y, ctr(c[1]), ROT_OUT[d], [c, o], y, y + BH,
             studs=True, studcells={c, o}))
for (name, c, d, g, h, cells) in SLOPES:
    y = -BH * (g + h)
    add(Part("02_felsen", name, rock_color(c, g=g), ctr(c[0]), y, ctr(c[1]), ROT_OUT[d], cells, y, y + BH * h,
             studs=True, studcells={c}))

# Kappen: Felskanten mit Curved/Cheese (Rauschen verteilt), Plattformen schwarz mit dunkelgrauem Rand,
# Laufweg als Dielen im Verband
caps = defaultdict(dict)
PLANKS = defaultdict(set)
for g in range(GMAX + 1):
    Sa = S[g + 1] if g + 1 <= GMAX else set()
    y = -BH * (g + 1)
    open_ = sorted(c for c in S[g] - Sa if (c, g + 1) not in covered and (c, g) not in replaced and c not in PILLAR_CELLS)
    openset, done = set(open_), set()
    for c in open_:
        if MAT[c] != "fels" or c in PLAT_CELLS or c in done: continue
        drop = [d for d in grad_dirs(c) if (c[0] + d[0], c[1] + d[1]) not in S[g]]
        if not drop or vnoise(c[0] + 0.5, c[1] + 0.5, 2.3, 11) < 0.5: continue
        d = drop[0]; i = (c[0] - d[0], c[1] - d[1])
        if i not in openset or i in done or MAT.get(i) != "fels" or i in PLAT_CELLS: continue
        add(Part("02_felsen", "11477", rock_color(c, top=True), (ctr(c[0]) + ctr(i[0])) / 2, y,
                 (ctr(c[1]) + ctr(i[1])) / 2, ROT_OUT[d], {c, i}, y - 16, y, studs=False))
        done |= {c, i}
    for c in open_:
        if c in done: continue
        if MAT[c] == "weg": PLANKS[g].add(c); continue
        if c in PLAT_CELLS:
            edge = any((c[0] + a, c[1] + b) not in PLAT_CELLS for a, b in DIRS)
            caps[(g, "04_plattformen")][c] = LBG if edge else DBG; continue
        drop = [d for d in grad_dirs(c) if (c[0] + d[0], c[1] + d[1]) not in S[g]]
        if drop and vnoise(c[0] + 0.5, c[1] + 0.5, 1.7, 8) < 0.75:
            add(Part("02_felsen", "54200", rock_color(c, top=True), ctr(c[0]), y, ctr(c[1]), ROT_OUT[drop[0]],
                     {c}, y - 16, y, studs=False))
            continue
        caps[(g, "02_felsen")][c] = rock_color(c, top=True)
for (g, sb), cc in caps.items():
    plates(sb, cc, -BH * (g + 1) - PH, g % 2, table=TILE, studs=False)
TILE_LEN = {1: "3070b", 2: "3069b", 3: "63864", 4: "2431", 6: "6636", 8: "4162"}
for g, cells in PLANKS.items():
    y = -BH * (g + 1) - PH
    for z in sorted({c[1] for c in cells}):
        xs = sorted(c[0] for c in cells if c[1] == z)
        runs, cur = [], [xs[0]]
        for x in xs[1:]:
            if x == cur[-1] + 1: cur.append(x)
            else: runs.append(cur); cur = [x]
        runs.append(cur)
        for run in runs:
            pos, first = 0, (2 if z % 2 else 4)
            while pos < len(run):
                n = min(first, len(run) - pos) if pos == 0 else min(4, len(run) - pos)
                while n not in TILE_LEN: n -= 1
                seg = run[pos:pos + n]; pos += n
                add(Part("03_laufweg", TILE_LEN[n], BLACK, sum(ctr(x) for x in seg) / n, y, ctr(z), 0,
                         {(x, z) for x in seg}, y, y + PH, studs=False))

# Durchgang: Boegen, darueber Steine bis zur Blockoberkante, oben Plattform-Fliesen
for x, z0, z1 in ARCHES:
    y = -BH * (ARCH_BOT + 2)
    cells = {(x, z) for z in range(z0, z1 + 1)}
    add(Part("05_block", "3307", DBG, ctr(x), y, (z0 + z1 + 1) / 2 * LDU, 90, cells, y, y + 2 * BH, studcells=cells))
for g in range(ARCH_BOT + 2, BLOCK_H):
    bricks("05_block", {c: (rock_color(c, g=g) if c[0] in BLOCK_X else BLACK) for c in BRIDGE}, g)
plates("04_plattformen", {c: DBG for c in BRIDGE}, -BH * BLOCK_H - PH, 1, table=TILE, studs=False)

# Augen und Muender
for c, g, d, col in EYES:
    y = -BH * (g + 1); rot = ROT_OUT[d]
    hl = add(Part("06_gesichter", "4070", rock_color(c, g=g), ctr(c[0]), y, ctr(c[1]), rot, {c}, y, y + BH))
    tx, tz = ctr(c[0]) + d[0] * 14, ctr(c[1]) + d[1] * 14
    o = (c[0] + d[0], c[1] + d[1])
    tile = add(Part("06_gesichter", "98138", col, tx, y + 10, tz, 0, {o}, y, y + 20, studs=False, hang=True,
                    extra=[f"1 {col} {fmt(tx)} {fmt(y + 10)} {fmt(tz)} {mat_str(rot)} 98138.dat"]))
    SNOT_LINKS.append((tile, hl))
for cells, g, d in MOUTHS:
    y = -BH * (g + 1); rot = ROT_OUT[d]
    cx = sum(ctr(c[0]) for c in cells) / 2; cz = sum(ctr(c[1]) for c in cells) / 2
    front = add(Part("06_gesichter", "11211", DBG, cx, y, cz, rot, set(cells), y, y + BH))
    gx, gz = cx + d[0] * 18, cz + d[1] * 18
    grille = add(Part("06_gesichter", "2412b", BLACK, gx, y + 10, gz, 0, {(c[0] + d[0], c[1] + d[1]) for c in cells},
                      y, y + 20, studs=False, hang=True, extra=[f"1 {BLACK} {fmt(gx)} {fmt(y + 10)} {fmt(gz)} {mat_str(rot)} 2412b.dat"]))
    SNOT_LINKS.append((grille, front))

# ---------------- Tuerme und Traversen-Raster ----------------
TRUSS_Y = -BH * 3 - 3 * 240 - 2 * PH       # Unterkante Traverse (= Oberkante Tuerme)
for X, Z in TOWERS:
    base = {(X + a, Z + b) for a in (-1, 0) for b in (-1, 0)}
    for g in range(3):
        pack("08_traverse", {c: BLACK for c in base}, BRICK, -BH * (g + 1), BH, g % 2)
    yy = -BH * 3
    for k in range(3):
        yy -= 240
        add(Part("08_traverse", "95347", DBG, X * LDU, yy, Z * LDU, 0 if Z < 0 else 180, base, yy, yy + 240))
        if k < 2:
            yy -= PH
            plates("08_traverse", {c: DBG for c in base}, yy, 1)
assert yy == TRUSS_Y
CROSS = [(-22, -21), (-11, -10), (-1, 0), (10, 11), (21, 22)]           # Quertraversen (x-Baender)
RING = {(i, k) for i in range(XMIN, XMAX + 1) for k in (-16, -15, 14, 15)} | \
       {(i, k) for i in (-32, -31, 30, 31) for k in range(ZMIN, ZMAX + 1)} | \
       {(i, k) for xs in CROSS for i in xs for k in range(ZMIN, ZMAX + 1)}

# ---------------- Ovaler Videoring (360 Grad) ----------------
RA, RB = 27.0, 12.6                          # Halbachsen (Noppen)
RING_BOT, RING_H = 22, 4                     # Unterkante (Steine), Hoehe
_ell = {c for c in GRID if ((c[0] + 0.5) / RA) ** 2 + ((c[1] + 0.5) / RB) ** 2 <= 1.0}
_outer = boundary8(_ell)
SCREEN = _outer | boundary8(_ell - _outer)   # Ring 2 Noppen dick (Verband ueber die Treppenecken)


def screen_color(c, r):
    """Bildinhalt: dunkle, verrauschte Endzeit-Landschaft; oben/unten dunkelgrauer Rahmen"""
    if r in (0, RING_H - 1): return DBG
    a = math.atan2((c[1] + 0.5) / RB, (c[0] + 0.5) / RA)
    n = vnoise(a * 9.0, r * 1.3, 1.0, 12)
    return WHITE if n > 0.62 else LBG if n > 0.45 else DBG if n > 0.3 else BLACK


for r in range(RING_H):
    g = RING_BOT + r
    for p in pack("07_videoring", {c: screen_color(c, r) for c in SCREEN}, BRICK, -BH * (g + 1), BH, r % 2):
        p.hang = True
RING_TOP_Y = -BH * (RING_BOT + RING_H)
# Aufhaengung: je Quertraverse und Seite zwei duenne Seile aus runden Steinen/Platten auf den aeusseren Ringzellen
HANGERS = []
for xs in CROSS:
    for sgn in (-1, 1):
        for x in xs:
            zs = [c[1] for c in _outer if c[0] == x and c[1] * sgn > 0]
            if zs: HANGERS.append((x, max(zs, key=lambda z: z * sgn)))
for c in HANGERS:
    gap = RING_TOP_Y - TRUSS_Y
    yy = RING_TOP_Y
    while gap >= BH:
        add(Part("07_videoring", "3062b", BLACK, ctr(c[0]), yy - BH, ctr(c[1]), 0, {c}, yy - BH, yy, hang=True))
        yy -= BH; gap -= BH
    while gap >= PH:
        add(Part("07_videoring", "6141", BLACK, ctr(c[0]), yy - PH, ctr(c[1]), 0, {c}, yy - PH, yy, hang=True))
        yy -= PH; gap -= PH
    assert yy == TRUSS_Y and gap == 0

y = TRUSS_Y - PH
t1 = plates("08_traverse", {c: DBG for c in RING}, y, 0)
for p in t1:
    if not (p.cells & RESERVED): p.hang = True
t2, nc = bond_layer("08_traverse", RING, t1, y - PH, DBG)
assert nc == 1, nc
y -= PH
POSTS = set()
for i in range(XMIN, XMAX + 1, 3):
    POSTS |= {(i, -16 if (i // 3) % 2 == 0 else -15), (i, 15 if (i // 3) % 2 == 0 else 14)}
for k in range(ZMIN, ZMAX + 1, 3):
    POSTS |= {(-32 if (k // 3) % 2 == 0 else -31, k), (31 if (k // 3) % 2 == 0 else 30, k)}
    for xs in CROSS: POSTS.add((xs[(k // 3) % 2], k))
POSTS |= {(XMIN, ZMIN), (XMIN, ZMAX), (XMAX, ZMIN), (XMAX, ZMAX)}
for L in range(2):
    yt = y - BH * (L + 1)
    for c in POSTS:
        add(Part("08_traverse", "3062b", DBG, ctr(c[0]), yt, ctr(c[1]), 0, {c}, yt, yt + BH))
y -= 2 * BH
t3 = plates("08_traverse", {c: DBG for c in RING}, y - PH, 1)
t4, nc = bond_layer("08_traverse", RING, t3, y - 2 * PH, DBG)
TRUSS_TOP = y - 2 * PH


def top_y(cells):
    return min([-BH * HF.get(c, 0) for c in cells] + [0])


SLING_LINKS = SNOT_LINKS

# ---------------- Fliegende Koepfe ----------------
# Dystopische Riesenkoepfe (Stein-Optik, hellgrau) haengen an den Quertraversen; Augen trans-rot (Laser).
# Aufbau von oben: Seil aus runden Steinen -> Schaedel -> Stirn mit Nasenwurzel -> Augen + Nase -> Wangen/Mund
# -> Kinn -> Hals. Alles haengt mit Klemmkraft von oben.
HEADS = [(-22, 0, 3, (-1, 0), 12), (-11, 3, 3, (0, 1), 11), (-1, 0, 5, (0, -1), 12), (10, -3, 3, (0, -1), 11),
         (21, 0, 3, (1, 0), 12)]                                   # (x, z Mitte, Groesse, Blickrichtung, Seil-Steine)


def head_layers(s):
    """Zellen je Lage relativ zur Mitte (u quer, v = Blickrichtung), von oben nach unten"""
    m = s // 2
    sq = [(u, v) for u in range(-m, m + 1) for v in range(-m, m + 1)]
    inner = [(u, v) for u in range(-m + 1, m) for v in range(-m + 1, m)] or [(0, 0)]
    eyes = [(-1, m), (1, m)]
    return [
        ("schaedel", {q: LBG for q in inner}),
        ("stirn", {q: LBG for q in sq}),
        ("augen", {q: LBG for q in sq if q != (0, m) and q not in eyes}),   # Nase (Slope) und Augen (SNOT) extra
        ("wangen", {q: (DBG if q == (0, m) else LBG) for q in sq}),                 # Mund dunkel
        ("kinn", {**{q: LBG for q in inner}, (0, m): LBG}),
    ]


for hx, hz, s_, fwd, rope in HEADS:
    side = (-fwd[1], fwd[0])
    def cell(q): return (hx + q[0] * side[0] + q[1] * fwd[0], hz + q[0] * side[1] + q[1] * fwd[1])
    yy = TRUSS_Y
    for k in range(rope):                                        # Seil: runde Steine 1x1 (Ursprung oben)
        add(Part("09_koepfe", "3062b", BLACK, ctr(hx), yy, ctr(hz), 0, {(hx, hz)}, yy, yy + BH, hang=True))
        yy += BH
    for L, (nm, lay) in enumerate(head_layers(s_)):
        cc = {cell(q): col for q, col in lay.items()}
        for p in pack("09_koepfe", cc, BRICK, yy, BH, L % 2): p.hang = True
        if nm == "stirn":                                        # Schaedel rund: Cheese-Slopes nach aussen
            m = s_ // 2; inner = set(head_layers(s_)[0][1])
            for (u, v) in lay:
                if (u, v) in inner: continue
                d = (0, 1) if v == m else (0, -1) if v == -m else (1, 0) if u == m else (-1, 0)
                wd = (d[0] * side[0] + d[1] * fwd[0], d[0] * side[1] + d[1] * fwd[1])
                c = cell((u, v))
                add(Part("09_koepfe", "54200", LBG, ctr(c[0]), yy, ctr(c[1]), ROT_OUT[wd], {c}, yy - 16, yy, studs=False))
        if nm == "augen":                                        # Glotzaugen: Headlight + runde Fliese weiss
            for q in ((-1, s_ // 2), (1, s_ // 2)):
                c = cell(q)
                hl = add(Part("09_koepfe", "4070", LBG, ctr(c[0]), yy, ctr(c[1]), ROT_OUT[fwd], {c}, yy, yy + BH, hang=True))
                tx, tz = ctr(c[0]) + fwd[0] * 14, ctr(c[1]) + fwd[1] * 14
                o = (c[0] + fwd[0], c[1] + fwd[1])
                t = add(Part("09_koepfe", "98138", WHITE, tx, yy + 10, tz, 0, {o}, yy, yy + 20, studs=False, hang=True,
                             extra=[f"1 {WHITE} {fmt(tx)} {fmt(yy + 10)} {fmt(tz)} {mat_str(ROT_OUT[fwd])} 98138.dat"]))
                SNOT_LINKS.append((t, hl))
        if nm == "augen":                                        # Nase: 45-Grad-Slope, faellt nach vorne ab
            m = s_ // 2; c0, c1 = cell((0, m)), cell((0, m + 1))
            add(Part("09_koepfe", "3040b", LBG, ctr(c0[0]), yy, ctr(c0[1]), ROT_OUT[fwd], [c0, c1], yy, yy + BH,
                     studcells={c0}, hang=True))
        yy += BH
    add(Part("09_koepfe", "3062b", DBG, ctr(hx), yy, ctr(hz), 0, {(hx, hz)}, yy, yy + BH, hang=True))   # Hals
    yy += BH
    assert yy < top_y({cell(q) for q in head_layers(s_)[1][1]}) - 2 * BH, (hx, hz)


# ---------------- Moving Heads am Traversen-Raster ----------------
BUSY = set(HANGERS) | {(hx, hz) for hx, hz, *_ in HEADS}
LIGHTS = []
for xs in CROSS:
    for z in (-13, -9, -6, 5, 8, 12):
        cells = {(xs[0] + a, z + b) for a in (0, 1) for b in (0, 1)}
        if cells & BUSY or not cells <= RING: continue
        yy = TRUSS_Y
        for name, col, h in (("3022", BLACK, PH), ("3941", BLACK, BH), ("4032a", TCLEAR, PH)):
            add(Part("11_licht", name, col, (xs[0] + 1) * LDU, yy, (z + 1) * LDU, 0, cells, yy, yy + h, hang=True))
            yy += h
        LIGHTS.append((xs[0], z)); BUSY |= cells

# ---------------- PA-Haenge ----------------
# In-the-round: PA an den Laengstraversen ausserhalb des Rings, Lautsprecher zeigen nach aussen zum Publikum
PA = [(x, z) for x in (-16, -5, 5, 16) for z in (-16, 14)]
for ax, az in PA:
    out = -1 if az < 0 else 1
    fz = az if out < 0 else az + 1                                # aeussere Spalte
    bz = fz - out                                                 # innere Spalte
    yy = TRUSS_Y
    add(Part("10_pa", "3022", DBG, ax * LDU, yy, (az + 1) * LDU, 0, {(ax + a, az + b) for a in (-1, 0) for b in (0, 1)},
             yy, yy + PH, hang=True))
    yy += PH
    for k in range(8):
        front = add(Part("10_pa", "11211", BLACK, ax * LDU, yy, ctr(fz), 0 if out < 0 else 180,
                         {(ax - 1, fz), (ax, fz)}, yy, yy + BH, hang=True))
        add(Part("10_pa", "3004", BLACK, ax * LDU, yy, ctr(bz), 0, {(ax - 1, bz), (ax, bz)}, yy, yy + BH, hang=True))
        gz = ctr(fz) + out * 18
        mat = "1 0 0 0 0 -1 0 1 0" if out < 0 else "1 0 0 0 0 1 0 -1 0"
        grille = add(Part("10_pa", "2412b", DBG, ax * LDU, yy + 10, gz, 0, {(ax - 1, fz + out), (ax, fz + out)},
                          yy, yy + 20, studs=False, hang=True,
                          extra=[f"1 {DBG} {fmt(ax * LDU)} {fmt(yy + 10)} {fmt(gz)} {mat} 2412b.dat"]))
        SNOT_LINKS.append((grille, front))
        yy += BH
        if k < 7:
            add(Part("10_pa", "3022", DBG, ax * LDU, yy, (az + 1) * LDU, 0,
                     {(ax + a, az + b) for a in (-1, 0) for b in (0, 1)}, yy, yy + PH, hang=True))
            yy += PH

# Grundplatten
for sx in (-1, 1):
    cells = {(i, k) for i in (range(0, 32) if sx > 0 else range(-32, 0)) for k in range(-16, 16)}
    add(Part("01_baseplates", "3811", BLACK, sx * 320, 0, 0, 0, cells, 0, 4, True))

TITLES = {"01_baseplates": "Grundplatten (2x 32x32)", "02_felsen": "Felswaende und Findlinge",
          "03_laufweg": "Gewundener Laufweg", "04_plattformen": "Plattform auf dem Block",
          "05_block": "Hoher Felsblock mit Durchgang", "06_gesichter": "Gesichter (SNOT-Augen und -Muender)",
          "07_videoring": "Ovaler Videoring (360 Grad)", "08_traverse": "Tuerme und Traversen-Raster",
          "09_koepfe": "Fliegende Koepfe", "10_pa": "PA-Haenge", "11_licht": "Moving Heads"}
print("Buehne:", len(MAT), "Zellen | Ueberhaenge", len(LIPS), "| Augen", len(EYES), "Muender", len(MOUTHS),
      "| Videoring", len(SCREEN), "Zellen,", len(HANGERS), "Seile | Scheinwerfer", len(LIGHTS))


# ---------------- Checks ----------------
def checks():
    idx_top = defaultdict(list)   # (ytop, cell) -> part index (Teile mit Noppen oben)
    for n, p in enumerate(parts):
        for c in p.studcells: idx_top[(p.ytop, c)].append(n)
    below = defaultdict(set); above = defaultdict(set)
    for n, p in enumerate(parts):
        if not p.cells: continue
        for c in p.cells:
            for m in idx_top.get((p.ybot, c), []):
                below[n].add(m); above[m].add(n)
    ground = {n for n, p in enumerate(parts) if p.name == "3811"}
    seen = set(ground); stack = list(ground)
    adj = defaultdict(set)
    for n in below:
        for m in below[n]: adj[n].add(m); adj[m].add(n)
    pid = {id(p): n for n, p in enumerate(parts)}
    for a, b in SLING_LINKS:                     # Truss liegt in den Seilschlingen
        adj[pid[id(a)]].add(pid[id(b)]); adj[pid[id(b)]].add(pid[id(a)])
    while stack:
        n = stack.pop()
        for m in adj[n]:
            if m not in seen: seen.add(m); stack.append(m)
    phys = [n for n, p in enumerate(parts) if p.cells]
    disconnected = [n for n in phys if n not in seen]
    floating = [n for n in phys if parts[n].name != "3811" and not below[n] and not parts[n].hang]
    hanging_ok = [n for n in phys if not below[n] and parts[n].hang and above[n]]
    # Zell-Unterstuetzung (streng) nur als Info
    unsup_cells = 0
    for n in phys:
        p = parts[n]
        if p.name == "3811" or p.hang: continue
        for c in p.cells:
            if not idx_top.get((p.ybot, c)): unsup_cells += 1
    # Kollisionen (8-LDU-Slabs)
    occ = {}; coll = []
    for n in phys:
        p = parts[n]
        if p.name == "3811": continue
        hit = False
        for c in p.cells:
            for yy in range(int(p.ytop), int(p.ybot), 2):
                key = (c, yy)
                if key in occ and not hit: coll.append((occ[key], n)); hit = True
                occ[key] = n
    print("parts:", len(parts))
    print("disconnected parts:", len(disconnected))
    print("floating parts (nichts darunter, nicht haengend):", len(floating))
    print("haengende Teile (Clutch von oben):", len(hanging_ok))
    print("unsupported cells (Info, streng pro Zelle):", unsup_cells)
    print("collisions:", len(coll))
    for n in (disconnected + floating)[:15]:
        p = parts[n]; print("  !", p.sub, p.name, p.color, p.x, p.y, p.z)
    for a, b in coll[:10]:
        print("  X", parts[a].sub, parts[a].name, parts[a].x, parts[a].y, parts[a].z, "<->", parts[b].sub, parts[b].name, parts[b].x, parts[b].y, parts[b].z)
    return len(disconnected) + len(floating) + len(coll)



# ---------------- Export ----------------
def export():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ldbbox", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "ldraw-render", "ldbbox.py"))
    names = {}
    try:
        lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)
        for nm in {p.name for p in parts}:
            try: names[nm] = lb.find(nm + ".dat").splitlines()[0][2:].strip().lstrip("~=")
            except Exception: names[nm] = nm
    except Exception:
        pass
    order = sorted({p.sub for p in parts})
    bysub = defaultdict(list)
    for p in parts: bysub[p.sub] += p.lines()
    out = [f"0 FILE {NAME}.ldr", "0 Travis Scott - Circus Maximus (UTOPIA) Stage (LEGO MOC)", f"0 Name: {NAME}.ldr",
           "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""]
    for s in order: out += [f"0 // {TITLES.get(s, s)}", f"1 16 0 0 0 {ROT[0]} {s}.ldr"]
    out += ["0 NOFILE"]
    for s in order:
        out += [f"0 FILE {s}.ldr", f"0 {TITLES.get(s, s)}", f"0 Name: {s}.ldr"] + bysub[s] + ["0 NOFILE"]
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f"{NAME}.mpd"), "w").write("\n".join(out) + "\n")
    bom = Counter((p.name, p.color) for p in parts)
    rows = ["LDraw Part,BrickLink ID,Name,Farbe,Menge"]; xml = ["<INVENTORY>"]
    for (nm, c), q in sorted(bom.items()):
        bl = BL_ID.get(nm, nm); cn, blc = COLORS[c]
        rows.append(f"{nm}.dat,{bl},\"{names.get(nm, nm)}\",{cn},{q}")
        xml.append(f"<ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID><COLOR>{blc}</COLOR><MINQTY>{q}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    open(os.path.join(OUT, f"{NAME}_bom.csv"), "w").write("\n".join(rows) + "\n")
    open(os.path.join(OUT, f"{NAME}_bricklink.xml"), "w").write("\n".join(xml) + "\n")
    print("TOTAL parts:", sum(bom.values()), "| Positionen:", len(bom))
    for s in order: print(f"  {s}: {sum(1 for p in parts if p.sub == s)}")


bad = checks()
export()
print("CHECK", "OK" if bad == 0 else f"FEHLER ({bad})")
