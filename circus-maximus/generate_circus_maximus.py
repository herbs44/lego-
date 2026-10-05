"""
Travis Scott – Circus Maximus Tour (UTOPIA) – LEGO MOC Generator
Langer, flacher Fels-Pfad durch die Arena (in-the-round) nach den Buehnenentwuerfen von Elsa Hanneke: grauer
Stein mit Felsgraten, runde Steinkoepfe mit Cartoon-Gesichtern (Kulleraugen, Nase, Grinsen, Ohren) zum Publikum,
hoher Felsblock mit Durchgang und Gesicht, Pyro, hoher ovaler 360-Grad-Videoring mit Feuerwand und Lampenreihe,
PA-Haenge, Traversen-Raster. Massstab: Minifig, 2 Baseplates 48x48.
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
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "3062b": "3062", "6141": "4073", "3815c01": "970c00", "63142": "x127c30pb01"}
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
COLORS.update({36: ("Trans-Red", 17), 57: ("Trans-Orange", 98), 25: ("Orange", 4),
               191: ("Bright Light Orange", 110)})
TRED, TORANGE, ORANGE, BLORANGE, TGREEN = 36, 57, 25, 191, 34
COLORS.update({34: ("Trans-Green", 20)})
# Farbkonzept nach den Fotos: grauer, verwitterter Stein (Dunkelgrau, Hellgrau im Licht, Schwarz in Spalten),
# schwarzer Buehnenboden, weisse Glotzaugen der Koepfe als hellster Punkt.
XMIN, XMAX, ZMIN, ZMAX = -48, 47, -24, 23
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
DECK = 3                                   # Laufweg (Steine) - Felsraender nur 1-3 Steine hoeher
PATH = [(-44.0, -3.0), (-19.5, -3.0), (-13.5, 1.5), (-6.0, -3.0), (1.5, 3.75), (9.0, -3.0), (22.5, 0.0), (43.0, 3.0)]
SX0, SX1 = -42, 41
BLOCK_X = (-42, -32)                       # hoher Felsblock
BLOCK_H = 18
BLOCK_CX = (BLOCK_X[0] + BLOCK_X[1] + 1) / 2
WALK_HW = 2.6                              # halbe Wegbreite (6 Zellen)
BOULDERS = []                              # alte Squircle-Findlinge -> ersetzt durch runde Steinkoepfe
HEAD_X = [(x, 1 if i % 2 else -1) for i, x in enumerate(range(-28, 40, 6))]   # runde Koepfe: (x links, Seite), Grundriss-Skizze
PED_H = DECK + 1                           # Sockel der Koepfe: 1 Stein ueber dem Weg
# Felsgrate ("faux-volcanic ridges"): hoehere Kaemme zwischen den Koepfen, Aussichtspunkte fuer den Performer
RIDGES = [(-20, -1, 2.6, 4.5), (4, -1, 2.6, 5.5), (28, -1, 2.4, 4.0), (-14, 1, 2.6, 4.0), (10, 1, 2.6, 5.0), (34, 1, 2.2, 3.5)]


def zc(x):
    """Mittellinie: gerade durch den Block, danach geschwungen (Skizze/Grundriss)"""
    if x <= -30.0: return -3.0
    return -3.0 + 4.2 * math.sin((x + 30.0) * 2 * math.pi / 34.0) + 1.2 * math.sin((x + 30.0) * 2 * math.pi / 13.0)


def in_block(x): return BLOCK_X[0] <= x < BLOCK_X[1] + 1


def half_width(x):
    if in_block(x): return 8.4 * math.sqrt(max(0.0, 1 - ((x - BLOCK_CX) / 7.5) ** 4))   # Ecken rund
    w = 5.6 + 1.0 * math.sin(0.37 * x + 0.3) + 0.7 * math.sin(0.87 * x)
    return w * min(1.0, (SX1 + 1 - x) / 3.0) if x > SX1 - 2 else w


def boulder(x, z):
    """Findlinge: runde Kuppen am Wegrand"""
    h = 0.0
    for bx, side in BOULDERS:
        bz = zc(bx) + side * (WALK_HW + 3.2)
        r = (abs(x - bx) ** 4 + abs(z - bz) ** 4) ** 0.25          # Squircle: flache Gesichtsseite
        if r < 3.3: h = max(h, DECK + 8.5 - r * 1.2)
    return h


def stage_f(p):
    """kontinuierliche Felshoehe (Steine); 0 = ausserhalb"""
    x, z = p
    if not (SX0 <= x <= SX1 + 1): return 0.0
    d = abs(z - zc(x)); W = half_width(x); b = boulder(x, z)
    if d <= WALK_HW: return float(DECK)
    if d > W: return b
    if in_block(x):                                                     # Kuppel: Rand faellt rund ab
        dn = d / W
        return BLOCK_H - (0.0 if dn < 0.45 else 30.0 * (dn - 0.45) ** 2) + 1.2 * (vnoise(x, z, 2.0, 5) - 0.5)
    h = DECK + 0.6 + 2.2 * vnoise(x, z, 3.9, 3) + 1.0 * vnoise(x, z, 1.9, 4)
    for rx, side, ln, hh in RIDGES:
        rz = zc(rx) + side * (WALK_HW + 2.8)
        e = ((x - rx) / ln) ** 2 + ((z - rz) / 1.9) ** 2
        if e < 1: h = max(h, DECK + 1 + hh * math.sqrt(1 - e) + 0.6 * (vnoise(x, z, 1.3, 6) - 0.5))
    return max(h, b)


# Ecktuerme + Mitte: je 1 Gittertraeger-Stapel (Rasterpunkt = Mitte 2x2)
TOWERS = [(-47, -23), (-47, 23), (47, -23), (47, 23), (0, -23), (0, 23)]
RESERVED = {(X + a, Z + b) for X, Z in TOWERS for a in (-1, 0) for b in (-1, 0)}
HF, MAT = {}, {}
for c in GRID:
    if c in RESERVED: continue
    p = (c[0] + 0.5, c[1] + 0.5)
    h = stage_f(p)
    if h <= 0.5: continue
    if abs(p[1] - zc(p[0])) <= WALK_HW and SX0 <= p[0] <= SX1 + 1: HF[c], MAT[c] = DECK, "weg"
    else: HF[c], MAT[c] = max(DECK + 1, int(math.floor(h + 0.5))), "fels"
for k in range(1, DECK):                                           # Treppen zum Hallenboden an beiden Enden
    for x in (SX0 - k, SX1 + k):
        for z in range(ZMIN, ZMAX + 1):
            if abs(z + 0.5 - zc(x + 0.5)) <= WALK_HW and (x, z) not in RESERVED: HF[(x, z)], MAT[(x, z)] = DECK - k, "weg"
# Oberseite des Blocks flach (Performer-Plattform wie auf dem Stadionfoto)
PLAT_CELLS = {c for c in HF if MAT[c] == "fels" and in_block(c[0] + 0.5) and abs(c[1] + 0.5 - zc(c[0] + 0.5)) < 4.2}
for c in PLAT_CELLS: HF[c] = BLOCK_H
# ---------------- Sockel fuer die runden Steinkoepfe ----------------
HEADS_R, HEAD_CELLS, HEAD_NEAR, HEAD_FRONT = [], set(), set(), set()   # (x links, z kleinste Reihe, Blickrichtung)
for hx, side in HEAD_X:
    zi = int(math.floor(zc(hx + 2.0) + side * (WALK_HW + 0.9)))
    rows = [zi + side * k for k in range(4)]
    cells = {(x, z) for x in range(hx, hx + 4) for z in rows}
    while any(MAT.get(c) == "weg" for c in cells):
        rows = [r + side for r in rows]; cells = {(x, z) for x in range(hx, hx + 4) for z in rows}
    if any(c in RESERVED or not (XMIN <= c[0] <= XMAX and ZMIN + 1 <= c[1] <= ZMAX - 1) for c in cells): continue
    for c in cells: HF[c], MAT[c] = PED_H, "fels"
    front = rows[-1]
    for x in range(hx - 1, hx + 5):                    # vor dem Gesicht: Fels unter Sockelhoehe
        for k in range(1, 7):
            c = (x, front + side * k)
            if MAT.get(c) == "fels": HF[c] = min(HF[c], PED_H - 1)
    for z in rows:                                     # neben den Ohren: Fels darunter, Slopes laufen nicht hinein
        for x, cap in ((hx - 1, PED_H - 1), (hx + 4, PED_H - 1), (hx - 2, PED_H), (hx + 5, PED_H)):
            if MAT.get((x, z)) == "fels": HF[(x, z)] = min(HF[(x, z)], cap)
    z0 = min(rows)
    HEADS_R.append((hx, z0, (0, side)))
    HEAD_CELLS |= cells
    HEAD_NEAR |= {(x, z) for x in range(hx - 1, hx + 5) for z in range(z0 - 1, z0 + 5)}
    HEAD_FRONT |= {(x, front + side * k) for x in range(hx - 1, hx + 5) for k in range(1, 4)}
LIFT = None
for x0 in (6, 7, 8, 5, 9, 4, 10, 11, 3):
    z0 = int(round(zc(x0 + 1.0) - 1.0))
    cs = {(x0 + a, z0 + b) for a in (0, 1) for b in (0, 1)}
    ring = {(x0 + a, z0 + b) for a in range(-1, 3) for b in range(-1, 3)} - cs
    if all(MAT.get(c) == "weg" and HF[c] == DECK for c in cs) and all(MAT.get(c) == "weg" for c in ring):
        LIFT = (x0, z0); break
assert LIFT, "kein Platz fuer den Lift"
LIFT_CELLS = {(LIFT[0] + a, LIFT[1] + b) for a in (0, 1) for b in (0, 1)}
for c in LIFT_CELLS: del HF[c], MAT[c]
STAIR_CELLS = set()
for rx, side, ln, hh in RIDGES:
    for x in (int(math.floor(rx)) - 1, int(math.floor(rx))):
        z = int(math.floor(zc(x + 0.5)))
        while MAT.get((x, z)) == "weg": z += side
        for k in range(12):
            c = (x, z + side * k)
            if MAT.get(c) != "fels" or c in HEAD_NEAR: break
            target = DECK + 1 + k
            if HF[c] <= target: break
            HF[c] = target; STAIR_CELLS.add(c)
TUNNEL = sorted(c for c in HF if MAT[c] == "weg" and in_block(c[0] + 0.5))
GMAX = max(HF.values())
S = [{c for c, h in HF.items() if h > g} for g in range(GMAX + 1)]

# Rockwork-Ueberhaenge an der Aussenkante: oberste Randlage kragt stellenweise 1 Noppe aus (umgedrehter Slope)
LIPS, _used = [], set()
for c in sorted(HF):
    if MAT[c] != "fels" or HF[c] < 3 or c in PLAT_CELLS: continue
    if in_block(c[0] + 0.5) or boulder(c[0] + 0.5, c[1] + 0.5) > 0 or c in HEAD_NEAR or c in STAIR_CELLS: continue
    g = HF[c] - 1
    if c not in S[g - 1] or vnoise(c[0] + 0.5, c[1] + 0.5, 2.2, 9) < 0.55: continue
    for d in DIRS:
        o = (c[0] + d[0], c[1] + d[1])
        if o in HF or o in RESERVED or o in _used or o in HEAD_NEAR or not (XMIN <= o[0] <= XMAX and ZMIN <= o[1] <= ZMAX): continue
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
        v = vnoise(p[0], p[1], 2.4, 1)
        return LBG if v > 0.7 else DBG if v > 0.22 else BLACK
    gx = stage_f((p[0] + 0.5, p[1])) - stage_f((p[0] - 0.5, p[1])); gz = stage_f((p[0], p[1] + 0.5)) - stage_f((p[0], p[1] - 0.5))
    gx, gz = max(-2.0, min(2.0, gx)), max(-2.0, min(2.0, gz))    # senkrechte Waende nicht ins Schwarze kippen
    n = (-gx, 1.0, -gz); L = math.sqrt(sum(v * v for v in n))
    shade = sum(a * b for a, b in zip(n, SUN)) / L
    shade += 0.4 * (vnoise(p[0] * 1.3, p[1] * 1.3 + (g or 0) * 0.12, 1.4, 7) - 0.5)   # senkrechte Streifen (Saeulen)
    return LBG if shade > 0.9 else DBG if shade > -0.1 else BLACK


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
ARCH_BOT = DECK + 6
ARCHES = []
for x in range(BLOCK_X[0], BLOCK_X[1] + 1):
    zs = [c[1] for c in TUNNEL if c[0] == x]
    z0, z1 = min(zs) - 1, max(zs) + 1
    assert z1 - z0 + 1 == 8, (x, zs)
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
    eyes = [outer_cell(x, side) for x in (-39, -35)]
    mouth = [outer_cell(x, side) for x in (-38, -37)]
    if None in eyes + mouth or len({c[1] for c in eyes + mouth}) != 1: continue
    ge = min(HF[c] for c in eyes) - 3; gm = ge - 4             # Lagen relativ zur Blockkante
    if all(free_face(c, ge, d) for c in eyes) and all(free_face(c, gm, d) for c in mouth):
        for c in eyes: EYES.append((c, ge, d, LBG)); replaced.add((c, ge))
        MOUTHS.append((tuple(mouth), gm, d)); replaced |= {(c, gm) for c in mouth}
# Reliefgesichter in den Aussenwaenden ("faces cut into stone"): Augen = Headlight-Steine (gemeisselte Hoehlen
# mit Noppe als Pupille), Nase = 45-Grad-Slope, Mund = schwarze Fliese auf Stein mit Seitennoppe
SMOUTHS, RELIEF = [], []
for side in (-1, 1):
    d = (0, side); last = -99
    for x0 in range(SX0 + 10, SX1 - 3):
        if x0 - last < 6: continue
        cs = [outer_cell(x0 + k, side) for k in range(3)]
        if None in cs or len({c[1] for c in cs}) != 1: continue
        if any(c in HEAD_NEAR or in_block(c[0] + 0.5) for c in cs): continue
        g = min(HF[c] for c in cs) - 1
        if g < 3: continue
        e1, m, e2 = cs
        n = (m[0] + d[0], m[1] + d[1])
        if not (free_face(e1, g, d) and free_face(e2, g, d) and free_face(m, g - 2, d)): continue
        if not (m in S[g - 1] and (m, g - 1) not in replaced and n not in HF and n not in RESERVED): continue
        EYES.append((e1, g, d, None)); EYES.append((e2, g, d, None)); replaced |= {(e1, g), (e2, g)}
        SMOUTHS.append((m, g - 2, d)); replaced.add((m, g - 2))
        RELIEF.append((x0, side)); last = x0
# Nasen (Osterinsel-Koepfe): 45-Grad-Slope mittig unter den Augen, kragt 1 Noppe aus der Wand
NOSES = []
for i in range(0, len(EYES) - 1, 2):
    (c1, g, d, _), (c2, _, _, _) = EYES[i], EYES[i + 1]
    if c1[1] != c2[1] or abs(c1[0] - c2[0]) < 2: continue
    for nx in sorted({(c1[0] + c2[0]) // 2, (c1[0] + c2[0] + 1) // 2}):
        c = (nx, c1[1]); n = (c[0] + d[0], c[1] + d[1])
        if c in S[g - 1] and (c, g - 1) not in replaced and n not in S[g - 1] and n not in HF and n not in RESERVED:
            NOSES.append((c, g - 1, d)); replaced.add((c, g - 1))

# ---------------- Slopes an Stufenkanten ----------------
STEP_PART = {1: "3040b", 2: "4286", 3: "60477"}
STEEP_PART = {2: "60481", 3: "4460b"}
covered, SLOPES = set(), []
for (c, o, d, g) in LIPS:
    replaced.add((c, g - 1)); covered.add((o, g - 1))
for g in range(0, GMAX + 1):
    for c in sorted(S[g]):
        if MAT[c] not in SLOPE_OK or (c, g) in replaced or c not in solid[g] or c in PLAT_CELLS \
                or c in PILLAR_CELLS or c in HEAD_CELLS or c in STAIR_CELLS: continue
        for d in grad_dirs(c):
            n = (c[0] + d[0], c[1] + d[1])
            if n in S[g]: continue
            below = S[g - 1] if g > 0 else set(GRID)
            if n not in below or (n, g) in covered or MAT.get(n) == "weg" or n in PILLAR_CELLS or n in LIP_O or n in HEAD_CELLS or n in STAIR_CELLS: continue
            if any((q, L) in replaced for q in (c, n) for L in range(g, g + 3)): continue
            run, q = [], n
            while q in below and q not in S[g] and (q, g) not in covered and len(run) < 3 and q not in RESERVED \
                    and MAT.get(q) != "weg" and q not in PILLAR_CELLS and q not in LIP_O and q not in HEAD_CELLS and q not in STAIR_CELLS \
                    and XMIN <= q[0] <= XMAX and ZMIN <= q[1] <= ZMAX:
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

# Textur: senkrechte Rillen wie gebrochene Basaltsaeulen - sichtbare Steine 1x2 werden stellenweise zu 2877
TEX = 0
for p_ in parts:
    if p_.sub not in ("02_felsen", "05_block") or p_.name != "3004" or p_.color not in (DBG, LBG): continue
    g_ = int(round(-p_.ytop / BH)) - 1
    xs_ = {c[0] for c in p_.cells}
    dirs_ = [(0, 1), (0, -1)] if len(xs_) == 2 else [(1, 0), (-1, 0)]
    if not any(all((c[0] + d[0], c[1] + d[1]) not in S[g_] for c in p_.cells) for d in dirs_): continue
    if vnoise(p_.x / LDU, p_.z / LDU + g_ * 0.7, 1.6, 21) > 0.55: p_.name = "2877"; TEX += 1

# Pyro-Punkte: alle 5 Noppen abwechselnd links/rechts auf der Felskante am Weg, dazu vorne auf dem Block
PYRO = []
def pyro_ok(c):
    if MAT.get(c) != "fels" or c in PLAT_CELLS or c in LIP_O or c in HEAD_NEAR or c in STAIR_CELLS: return None
    g = HF[c] - 1
    if (c, g) in replaced or (c, g + 1) in covered or c not in solid[g]: return None
    if g + 1 <= GMAX and c in S[g + 1]: return None
    if any(abs(c[0] - q[0]) + abs(c[1] - q[1]) < 3 for q, _ in PYRO): return None
    return g


for i, x0 in enumerate(range(SX0 + 13, SX1 - 1, 5)):
    done_ = False
    for side in ((1, -1) if i % 2 else (-1, 1)):
        for x in (x0, x0 + 1, x0 - 1, x0 + 2, x0 - 2):
            for dz in (3, 4, 5, 6, 7, 8, 9):
                c = (x, int(math.floor(zc(x + 0.5) + side * dz)))
                g = pyro_ok(c)
                if g is not None: PYRO.append((c, g)); done_ = True; break
            if done_: break
        if done_: break
_pz = sorted(PLAT_CELLS)
for c in [min((q for q in _pz if q[0] == BLOCK_X[0]), key=lambda q: q[1]), max((q for q in _pz if q[0] == BLOCK_X[0]), key=lambda q: q[1])]:
    PYRO.append((c, BLOCK_H - 1))
PYRO_CELLS = {c for c, g in PYRO}

# Bodenmonitore: Cheese-Slope 1x2 schwarz am Wegrand, Schraege zur Wegmitte
MONITORS = []
for i, x in enumerate(range(SX0 + 13, SX1 - 3, 8)):
    side = 1 if i % 2 else -1
    for dz in (2.1, 1.1):
        z = int(math.floor(zc(x + 1.0) + side * dz))
        cc = [(x, z), (x + 1, z)]
        if all(MAT.get(q) == "weg" and HF[q] == DECK for q in cc):
            MONITORS.append((cc, side)); break
MON_CELLS = {q for cc, _ in MONITORS for q in cc}

# Kappen: Felskanten mit Curved/Cheese (Rauschen verteilt), Plattformen schwarz mit dunkelgrauem Rand,
# Laufweg als Dielen im Verband
caps = defaultdict(dict)
PLANKS = defaultdict(set)
BOULDERS2, SPIRES, EMBERS, ROCKSPOTS = [], [], [], []
for g in range(GMAX + 1):
    Sa = S[g + 1] if g + 1 <= GMAX else set()
    y = -BH * (g + 1)
    open_ = sorted(c for c in S[g] - Sa if (c, g + 1) not in covered and (c, g) not in replaced and c not in PILLAR_CELLS
                   and c not in PYRO_CELLS and c not in HEAD_CELLS)
    openset, done = set(open_), set()
    # Felskugeln: runde Steine 2x2 mit Kuppel auf freien 2x2-Flaechen (Echo der Koepfe)
    for c in open_:
        if g < DECK - 1 or MAT[c] != "fels" or c in PLAT_CELLS or c in HEAD_NEAR or c in HEAD_FRONT or c in done \
                or c in STAIR_CELLS: continue
        sq = [(c[0] + a, c[1] + b) for a in (0, 1) for b in (0, 1)]
        if not all(q in openset and q not in done and MAT.get(q) == "fels" and q not in PLAT_CELLS and q not in HEAD_NEAR
                   and q not in HEAD_FRONT and q not in STAIR_CELLS for q in sq): continue
        if vnoise(c[0] + 0.5, c[1] + 0.5, 1.3, 35) < 0.5: continue
        tall = vnoise(c[0], c[1], 2.0, 36) > 0.5
        add(Part("02_felsen", "30151b" if tall else "30367c", rock_color(c, top=True) if rock_color(c, top=True) != BLACK else DBG,
                 (c[0] + 1) * LDU, y - (40 if tall else BH), (c[1] + 1) * LDU, 0, set(sq), y - (40 if tall else BH), y, studs=False))
        BOULDERS2.append(c); done |= set(sq)
    for c in open_:                                     # Felsspitzen und Glut zuerst verteilen
        if g < DECK - 1 or MAT[c] != "fels" or c in PLAT_CELLS or c in HEAD_NEAR or c in HEAD_FRONT or c in done \
                or c in STAIR_CELLS: continue
        if any(abs(c[0] - q[0]) + abs(c[1] - q[1]) < 3 for q, _ in SPIRES[-8:]): continue
        if any(MAT.get((c[0] + a, c[1] + b)) == "weg" for a, b in DIRS) and vnoise(c[0] + 0.5, c[1] + 0.5, 1.0, 47) > 0.45\
                and not any(abs(c[0] - q[0]) + abs(c[1] - q[1]) < 4 for q, _ in ROCKSPOTS):
            ROCKSPOTS.append((c, g)); done.add(c); continue
        if vnoise(c[0] + 0.5, c[1] + 0.5, 1.1, 37) > 0.62: SPIRES.append((c, g)); done.add(c); continue
        if vnoise(c[0] + 0.5, c[1] + 0.5, 0.9, 41) > 0.76: EMBERS.append((c, g)); done.add(c)
    for c in open_:
        if MAT[c] != "fels" or c in PLAT_CELLS or c in done or c in STAIR_CELLS: continue
        drop = [d for d in grad_dirs(c) if (c[0] + d[0], c[1] + d[1]) not in S[g]]
        if not drop or vnoise(c[0] + 0.5, c[1] + 0.5, 2.3, 11) < 0.5: continue
        d = drop[0]; i = (c[0] - d[0], c[1] - d[1])
        if i not in openset or i in done or MAT.get(i) != "fels" or i in PLAT_CELLS or i in STAIR_CELLS: continue
        add(Part("02_felsen", "11477", rock_color(c, top=True), (ctr(c[0]) + ctr(i[0])) / 2, y,
                 (ctr(c[1]) + ctr(i[1])) / 2, ROT_OUT[d], {c, i}, y - 16, y, studs=False))
        done |= {c, i}
    for c in open_:
        if c in done: continue
        if MAT[c] == "weg":
            if c not in MON_CELLS: PLANKS[g].add(c)
            continue
        if c in STAIR_CELLS:                                 # Stufen: glatte Fliesen wie der Weg
            caps[(g, "03_laufweg")][c] = DBG; continue
        if c in PLAT_CELLS:
            edge = any((c[0] + a, c[1] + b) not in PLAT_CELLS for a, b in DIRS)
            caps[(g, "04_plattformen")][c] = LBG if edge else DBG; continue
        drop = [d for d in grad_dirs(c) if (c[0] + d[0], c[1] + d[1]) not in S[g]]
        if drop and vnoise(c[0] + 0.5, c[1] + 0.5, 1.7, 8) < 0.75:
            add(Part("02_felsen", "54200", rock_color(c, top=True), ctr(c[0]), y, ctr(c[1]), ROT_OUT[drop[0]],
                     {c}, y - 16, y, studs=False))
            continue
        caps[(g, "02_felsen")][c] = rock_color(c, top=True)
for c, g in SPIRES:
    y = -BH * (g + 1)
    n2 = 2 if vnoise(c[0], c[1], 1.7, 38) > 0.55 else 1
    for k in range(n2):
        add(Part("02_felsen", "3062b", DBG if k == 0 else rock_color(c, top=True), ctr(c[0]), y - BH * (k + 1), ctr(c[1]), 0,
                 {c}, y - BH * (k + 1), y - BH * k))
    add(Part("02_felsen", "4589", DBG, ctr(c[0]), y - BH * (n2 + 1), ctr(c[1]), 0, {c}, y - BH * (n2 + 1), y - BH * n2,
             studs=False))
for c, g in ROCKSPOTS:
    y = -BH * (g + 1)
    add(Part("02_felsen", "3062b", BLACK, ctr(c[0]), y - BH, ctr(c[1]), 0, {c}, y - BH, y))
    add(Part("02_felsen", "6141", TCLEAR, ctr(c[0]), y - BH - PH, ctr(c[1]), 0, {c}, y - BH - PH, y - BH))
for c, g in EMBERS:
    y = -BH * (g + 1)
    add(Part("02_felsen", "98138", TORANGE, ctr(c[0]), y - PH, ctr(c[1]), 0, {c}, y - PH, y, studs=False))
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
                vv = vnoise(seg[0] + 0.5 + n * 0.3, z + 0.5, 1.2, 43)
                pc = LBG if vv > 0.74 else BLACK if vv < 0.22 else DBG
                add(Part("03_laufweg", TILE_LEN[n], pc, sum(ctr(x) for x in seg) / n, y, ctr(z), 0,
                         {(x, z) for x in seg}, y, y + PH, studs=False))

for cc, side in MONITORS:
    y = -BH * DECK
    add(Part("03_laufweg", "85984", BLACK, (cc[0][0] + 1) * LDU, y, ctr(cc[0][1]), 0 if side > 0 else 180, set(cc),
             y - 16, y, studs=False))

# Durchgang: Boegen, darueber Steine bis zur Blockoberkante, oben Plattform-Fliesen
for x, z0, z1 in ARCHES:
    y = -BH * (ARCH_BOT + 2)
    cells = {(x, z) for z in range(z0, z1 + 1)}
    add(Part("05_block", "16577", DBG, ctr(x), y, (z0 + z1 + 1) / 2 * LDU, 90, cells, y, y + 2 * BH, studcells=cells))
for g in range(ARCH_BOT + 2, BLOCK_H):
    bricks("05_block", {c: (rock_color(c, g=g) if c[0] in BLOCK_X else BLACK) for c in BRIDGE}, g)
plates("04_plattformen", {c: DBG for c in BRIDGE}, -BH * BLOCK_H - PH, 1, table=TILE, studs=False)

# Augen und Muender
for c, g, d, col in EYES:
    y = -BH * (g + 1); rot = ROT_OUT[d]
    if col is None:                       # Reliefgesicht: gemeisselte Augenhoehle
        add(Part("06_gesichter", "4070", rock_color(c, g=g), ctr(c[0]), y, ctr(c[1]), rot, {c}, y, y + BH))
        continue
    # Block: grosse, flache Augenscheiben (Rundfliese 2x2 dunkelgrau) mittig auf der Seitennoppe eines Steins 1x1
    hl = add(Part("06_gesichter", "87087", rock_color(c, g=g), ctr(c[0]), y, ctr(c[1]), rot, {c}, y, y + BH))
    tx, tz = ctr(c[0]) + d[0] * 18, ctr(c[1]) + d[1] * 18
    t_ = (abs(d[1]), abs(d[0]))
    oc = {(c[0] + d[0] + k * t_[0], c[1] + d[1] + k * t_[1]) for k in (-1, 0, 1)}
    tile = add(Part("06_gesichter", "14769", BLACK, tx, y + 10, tz, 0, oc, y - 10, y + 30, studs=False, hang=True,
                    extra=[f"1 {BLACK} {fmt(tx)} {fmt(y + 10)} {fmt(tz)} {mat_str(rot)} 14769.dat"]))
    SNOT_LINKS.append((tile, hl))
for c, g, d in NOSES:
    y = -BH * (g + 1); n = (c[0] + d[0], c[1] + d[1])
    add(Part("06_gesichter", "3040b", rock_color(c, g=g), ctr(c[0]), y, ctr(c[1]), ROT_OUT[d], [c, n], y, y + BH,
             studcells={c}))
for c, g, d in SMOUTHS:
    y = -BH * (g + 1); rot = ROT_OUT[d]
    fr = add(Part("06_gesichter", "87087", DBG, ctr(c[0]), y, ctr(c[1]), rot, {c}, y, y + BH))
    tx, tz = ctr(c[0]) + d[0] * 18, ctr(c[1]) + d[1] * 18
    o = (c[0] + d[0], c[1] + d[1])
    tl = add(Part("06_gesichter", "3070b", BLACK, tx, y + 10, tz, 0, {o}, y, y + 20, studs=False, hang=True,
                  extra=[f"1 {BLACK} {fmt(tx)} {fmt(y + 10)} {fmt(tz)} {mat_str(rot)} 3070b.dat"]))
    SNOT_LINKS.append((tl, fr))
for cells, g, d in MOUTHS:
    y = -BH * (g + 1); rot = ROT_OUT[d]
    cx = sum(ctr(c[0]) for c in cells) / 2; cz = sum(ctr(c[1]) for c in cells) / 2
    front = add(Part("06_gesichter", "11211", DBG, cx, y, cz, rot, set(cells), y, y + BH))
    gx, gz = cx + d[0] * 18, cz + d[1] * 18
    grille = add(Part("06_gesichter", "2412b", BLACK, gx, y + 10, gz, 0, {(c[0] + d[0], c[1] + d[1]) for c in cells},
                      y, y + 20, studs=False, hang=True, extra=[f"1 {BLACK} {fmt(gx)} {fmt(y + 10)} {fmt(gz)} {mat_str(rot)} 2412b.dat"]))
    SNOT_LINKS.append((grille, front))

# ---------------- Runde Steinkoepfe (Osterinsel trifft Cartoon) ----------------
# 4x4 Noppen, 3 Steine + Platte + Kuppel (120 LDU): runde Ecken (Rundstein 1x1), vorne SNOT-Gesicht:
# Mund = schwarze Fliese 1x2, Nase = Cheese-Slope 1x2 (kragt nach unten aus), Augen = runde Fliesen 1x1 schwarz,
# Ohren = Rundplatten 2x2 auf Steinen mit Seitennoppe, oben Kuppel 4x4.
def m_nose(d):
    dx, dz = d
    return [[dz, -dx, 0], [0, 0, 1], [-dx, -dz, 0]]


def snot(sub, name, col, x, y, z, M, cells, ytop, ybot, holder):
    e = add(Part(sub, name, col, x, y, z, 0, cells, ytop, ybot, studs=False, hang=True,
                 extra=[f"1 {col} {fmt(x)} {fmt(y)} {fmt(z)} " + " ".join(fmt(round(M[i][j], 4)) for i in range(3) for j in range(3)) + f" {name}.dat"]))
    SNOT_LINKS.append((e, holder))
    return e


def front_mat(d):
    R = RM[ROT_OUT[d]]
    return [[sum(R[i][k] * M_FRONT[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


HEADCOL = LBG
for hx, z0, d in HEADS_R:
    def cell(u, v, hx=hx, z0=z0, d=d):
        return (hx + u, z0 + v) if d[1] < 0 else (hx + 3 - u, z0 + 3 - v)
    udir = (1, 0) if d[1] < 0 else (-1, 0)
    yb = -BH * PED_H
    def brick(name, uv, ytop, rot=None, col=HEADCOL):
        cs = [cell(u, v) for u, v in uv]
        cx = sum(ctr(c[0]) for c in cs) / len(cs); cz = sum(ctr(c[1]) for c in cs) / len(cs)
        if rot is None: rot = 0 if len({c[0] for c in cs}) >= len({c[1] for c in cs}) else 90
        return add(Part("09_koepfe", name, col, cx, ytop, cz, rot, set(cs), ytop, ytop + BH))
    def mid(cs): return (sum(ctr(c[0]) for c in cs) / len(cs), sum(ctr(c[1]) for c in cs) / len(cs))
    fr = [cell(1, 0), cell(2, 0)]
    fo = {(c[0] + d[0], c[1] + d[1]) for c in fr}
    for L in range(3):
        yt = yb - BH * (L + 1)
        for uv in ((0, 3), (3, 3)): brick("3062b", [uv], yt)
        brick("3004", [(1, 3), (2, 3)], yt)
        if L == 1:                                        # Ohren-Lage
            brick("3003", [(1, 1), (2, 1), (1, 2), (2, 2)], yt)
            brick("3005", [(0, 2)], yt); brick("3005", [(3, 2)], yt)
            for u, sgn in ((0, -1), (3, 1)):
                sd = (udir[0] * sgn, udir[1] * sgn)
                h = brick("87087", [(u, 1)], yt, rot=ROT_OUT[sd])
                c = cell(u, 1)
                ex, ez = ctr(c[0]) + sd[0] * 18, ctr(c[1]) + sd[1] * 18
                oc = {(cell(u, v)[0] + sd[0], cell(u, v)[1] + sd[1]) for v in (0, 1, 2)}
                snot("09_koepfe", "14769", HEADCOL, ex, yt + 10, ez, front_mat(sd), oc, yt - 10, yt + 30, h)
        else:
            brick("3001", [(u, v) for u in range(4) for v in (1, 2)], yt)
        if L == 0:                                        # breites Grinsen: Fliese 1x4 schwarz
            row = [cell(u, 0) for u in range(4)]
            h = brick("30414", [(u, 0) for u in range(4)], yt, rot=ROT_OUT[d])
            mx, mz = mid(row)
            snot("09_koepfe", "2431", DBG, mx + d[0] * 18, yt + 10, mz + d[1] * 18, front_mat(d),
                 {(c[0] + d[0], c[1] + d[1]) for c in row}, yt, yt + 20, h)
        else:                                             # runde Ecken, Mitte: Nase / Augen
            brick("3005", [(0, 0)], yt); brick("3005", [(3, 0)], yt)
            h = brick("11211", [(1, 0), (2, 0)], yt, rot=ROT_OUT[d])
            mx, mz = mid(fr)
            if L == 1:
                snot("09_koepfe", "85984", HEADCOL, mx + d[0] * 10, yt + 10, mz + d[1] * 10, m_nose(d), fo, yt, yt + 20, h)
            else:                                         # Augen: Headlight-Steine = gemeisselte Hoehlen
                parts.remove(h)
                for uv in ((1, 0), (2, 0)): brick("4070", [uv], yt, rot=ROT_OUT[d])
    yt = yb - 3 * BH - PH
    allc = {cell(u, v) for u in range(4) for v in range(4)}
    cx, cz = mid(list(allc))
    add(Part("09_koepfe", "3031", HEADCOL, cx, yt, cz, 0, allc, yt, yt + PH))
    dome = "30208" if len(HEADS_R) and (hx // 6) % 3 == 0 else "86500"   # jede dritte Kuppel facettiert (Risse)
    add(Part("09_koepfe", dome, HEADCOL, cx, yt, cz, ROT_OUT[d], allc, yt - 40, yt, studs=False))

# ---------------- Pyro-Flammen ----------------
# Pyro-Einheit: runder Stein 1x1 schwarz (Duese), darin steckt die Flamme 7L mit Stange (85959) in der
# Hohlnoppe - Stange in Hohlnoppe ist eine legale Verbindung. Abwechselnd Trans-Orange und Trans-Gelb.
for k, (c, g) in enumerate(PYRO):
    y = -BH * (g + 1)
    add(Part("12_pyro", "3062b", BLACK, ctr(c[0]), y - BH, ctr(c[1]), 0, {c}, y - BH, y))
    fy = y - BH - 4
    add(Part("12_pyro", "85959", (TCLEAR, TORANGE, TYELLOW)[k % 3], ctr(c[0]), fy, ctr(c[1]), (k * 90) % 360, {c},
             fy - 134, y - BH, studs=False))

# ---------------- Bodenlautsprecher (Subs/Front-Fills) ----------------
FLOOR_USED = set()


def floor_free(cells):
    return all(q not in HF and q not in RESERVED and q not in FLOOR_USED and XMIN <= q[0] <= XMAX and ZMIN <= q[1] <= ZMAX
               and not any((q[0] + a, q[1] + b) in HF for a, b in N8) for q in cells)


SUBS = []
for x in range(SX0 + 5, SX1 - 3, 9):
    for side in (-1, 1):
        for off in (3.0, 4.0, 5.0, 6.0, 7.0):
            fz = int(math.floor(zc(x + 1.0) + side * (half_width(x + 1.0) + off)))
            bz = fz - side
            cells = {(x, fz), (x + 1, fz), (x, bz), (x + 1, bz)}
            front = {(x, fz + side), (x + 1, fz + side)}
            if floor_free(cells | front) and not any((q, L) in covered for q in cells | front for L in range(3)): break
        else: continue
        rot = ROT_OUT[(0, side)]
        for L in range(2):
            yy = -BH * (L + 1)
            fr = add(Part("13_boden", "11211", BLACK, (x + 1) * LDU, yy, ctr(fz), rot, {(x, fz), (x + 1, fz)}, yy, yy + BH))
            add(Part("13_boden", "3004", BLACK, (x + 1) * LDU, yy, ctr(bz), 0, {(x, bz), (x + 1, bz)}, yy, yy + BH))
            gz = ctr(fz) + side * 18
            gr = add(Part("13_boden", "2412b", DBG, (x + 1) * LDU, yy + 10, gz, 0, front, yy, yy + 20, studs=False, hang=True,
                          extra=[f"1 {DBG} {fmt((x + 1) * LDU)} {fmt(yy + 10)} {fmt(gz)} {mat_str(rot)} 2412b.dat"]))
            SNOT_LINKS.append((gr, fr))
        yy = -BH * 2 - PH
        add(Part("13_boden", "3068b", BLACK, (x + 1) * LDU, yy, (fz + bz + 1) / 2 * LDU, 0, cells, yy, yy + PH, studs=False))
        FLOOR_USED |= cells | front
        SUBS.append((x, fz))

# ---------------- Uplights: rote Bodenstrahler am Felsfuss ----------------
UPLIGHTS = []
for i, x in enumerate(range(SX0 + 2, SX1, 3)):
    side = 1 if i % 2 else -1
    for dz in range(3, 14):
        c = (x, int(math.floor(zc(x + 0.5) + side * dz)))
        if c in HF: continue
        if c in RESERVED or c in FLOOR_USED or any((c, L) in covered for L in range(4)) \
                or not (XMIN <= c[0] <= XMAX and ZMIN <= c[1] <= ZMAX): continue
        add(Part("13_boden", "6141", BLACK, ctr(c[0]), -PH, ctr(c[1]), 0, {c}, -PH, 0))
        add(Part("13_boden", "98138", TCLEAR, ctr(c[0]), -2 * PH, ctr(c[1]), 0, {c}, -2 * PH, -PH, studs=False))
        FLOOR_USED.add(c); UPLIGHTS.append(c)
        break

# ---------------- Lift: Hubsaeule im Schacht, oben eine schwarze Klappe buendig mit dem Weg ----------------
SUB_NOTES = defaultdict(list)
for g in range(DECK):
    add(Part("16_lift", "3003", BLACK, (LIFT[0] + 1) * LDU, -BH * (g + 1), (LIFT[1] + 1) * LDU, 0, LIFT_CELLS,
             -BH * (g + 1), -BH * g))
add(Part("16_lift", "3068b", BLACK, (LIFT[0] + 1) * LDU, -BH * DECK - PH, (LIFT[1] + 1) * LDU, 0, LIFT_CELLS,
         -BH * DECK - PH, -BH * DECK, studs=False))
SUB_NOTES["16_lift"].append(f"0 // LIFT {fmt((LIFT[0] + 1) * LDU)} {fmt(-BH * DECK - PH)} {fmt((LIFT[1] + 1) * LDU)}")

# ---------------- Geroell am Felsfuss ----------------
RUBBLE = []
for c in sorted(GRID):
    if c in HF or c in RESERVED or c in FLOOR_USED or any((c, L) in covered for L in range(3)): continue
    nb = [(c[0] + a, c[1] + b) for a, b in N8]
    if not any(q in HF and MAT[q] == "fels" for q in nb) or any(MAT.get(q) == "weg" for q in nb): continue
    v = vnoise(c[0] + 0.5, c[1] + 0.5, 0.8, 49)
    if v < 0.55: continue
    col = DBG if v < 0.8 else (LBG if v < 0.9 else BLACK)
    if v > 0.7:
        d = next((dd for dd in DIRS if (c[0] - dd[0], c[1] - dd[1]) in HF), DIRS[0])
        add(Part("13_boden", "54200", col, ctr(c[0]), 0, ctr(c[1]), ROT_OUT[d], {c}, -16, 0, studs=False))
    else:
        add(Part("13_boden", "6141", col, ctr(c[0]), -PH, ctr(c[1]), 0, {c}, -PH, 0))
    RUBBLE.append(c)

# ---------------- Tuerme und Traversen-Raster ----------------
TRUSS_Y = -BH * 3 - 4 * 240 - 3 * PH       # Unterkante Traverse (= Oberkante Tuerme)
for X, Z in TOWERS:
    base = {(X + a, Z + b) for a in (-1, 0) for b in (-1, 0)}
    for g in range(3):
        pack("08_traverse", {c: BLACK for c in base}, BRICK, -BH * (g + 1), BH, g % 2)
    yy = -BH * 3
    for k in range(4):
        yy -= 240
        add(Part("08_traverse", "95347", BLACK, X * LDU, yy, Z * LDU, 0 if Z < 0 else 180, base, yy, yy + 240))
        if k < 3:
            yy -= PH
            plates("08_traverse", {c: BLACK for c in base}, yy, 1)
assert yy == TRUSS_Y
CROSS = [(-33, -32), (-17, -16), (-1, 0), (15, 16), (31, 32)]           # Quertraversen (x-Baender)
RING = {(i, k) for i in range(XMIN, XMAX + 1) for k in (-24, -23, 22, 23)} | \
       {(i, k) for i in (-48, -47, 46, 47) for k in range(ZMIN, ZMAX + 1)} | \
       {(i, k) for xs in CROSS for i in xs for k in range(ZMIN, ZMAX + 1)}

# ---------------- Ovaler Videoring (360 Grad) ----------------
RA, RB = 40.5, 19.0                          # Halbachsen (Noppen)
RING_BOT, RING_H = 31, 8                     # Unterkante (Steine), Hoehe: hohes Band wie auf den Fotos
_ell = {c for c in GRID if ((c[0] + 0.5) / RA) ** 2 + ((c[1] + 0.5) / RB) ** 2 <= 1.0}
_outer = boundary8(_ell)
SCREEN = _outer | boundary8(_ell - _outer)   # Ring 2 Noppen dick (Verband ueber die Treppenecken)
def _ev(c): return ((c[0] + 0.5) / RA) ** 2 + ((c[1] + 0.5) / RB) ** 2
for _ in range(3):                           # nur diagonal verbundene Stellen mit einer Zelle schliessen
    for c in sorted(SCREEN):
        for a, b in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            if (c[0] + a, c[1] + b) in SCREEN and (c[0] + a, c[1]) not in SCREEN and (c[0], c[1] + b) not in SCREEN:
                SCREEN.add(min(((c[0] + a, c[1]), (c[0], c[1] + b)), key=_ev))


def screen_color(c, r):
    """Bildinhalt: Feuerwand (UTOPIA-Visuals) - unten gelb/orange, nach oben rot bis schwarz; Rahmen dunkelgrau"""
    if r in (0, RING_H - 1): return BLACK
    a = math.atan2((c[1] + 0.5) / RB, (c[0] + 0.5) / RA)
    t = (r - 1) / (RING_H - 3)                                   # 0 unten .. 1 oben
    flame = 0.6 * vnoise(a * 16.0, 0.5, 1.0, 12) + 0.4 * vnoise(a * 41.0, 2.5, 1.0, 13)   # Flammenzungen
    heat = 1.25 * flame - 1.05 * t + 0.3
    return YELLOW if heat > 0.85 else BLORANGE if heat > 0.65 else ORANGE if heat > 0.45 else RED if heat > 0.25 \
        else DKRED if heat > 0.08 else BLACK


# Aufbau von unten: Rahmenlage, Verbund-Plattenlage, Bildlagen, Verbund-Plattenlage, Rahmenlage.
# Die Plattenlagen verbinden alle Steine des Rings zu einem Stueck (sonst bleiben an Treppenecken Inseln).
yy = -BH * RING_BOT
lower = None
for r in range(RING_H):
    lay = pack("07_videoring", {c: screen_color(c, r) for c in SCREEN}, BRICK, yy - BH, BH, r % 2)
    for p in lay: p.hang = True
    yy -= BH
    if r in (0, RING_H - 2):
        bl, nc = bond_layer("07_videoring", set(SCREEN), lay, yy - PH, DBG)   # Gesamtverbund prueft checks()
        for p in bl: p.hang = True
        yy -= PH
RING_TOP_Y = yy
# Lampenreihe unter dem Ring (Spots wie auf den Fotos): jede dritte Zelle der Innenseite
RING_LAMPS = []
for i, c in enumerate(sorted(SCREEN - _outer, key=lambda c: math.atan2((c[1] + 0.5) / RB, (c[0] + 0.5) / RA))):
    if i % 3: continue
    yl = -BH * RING_BOT
    add(Part("07_videoring", "3062b", BLACK, ctr(c[0]), yl, ctr(c[1]), 0, {c}, yl, yl + BH, hang=True))
    add(Part("07_videoring", "6141", TCLEAR, ctr(c[0]), yl + BH, ctr(c[1]), 0, {c}, yl + BH, yl + BH + PH, hang=True))
    RING_LAMPS.append(c)
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
t1 = plates("08_traverse", {c: BLACK for c in RING}, y, 0)
for p in t1:
    if not (p.cells & RESERVED): p.hang = True
t2, nc = bond_layer("08_traverse", RING, t1, y - PH, BLACK)
assert nc == 1, nc
y -= PH
POSTS = set()
for i in range(XMIN, XMAX + 1, 3):
    POSTS |= {(i, -24 if (i // 3) % 2 == 0 else -23), (i, 23 if (i // 3) % 2 == 0 else 22)}
for k in range(ZMIN, ZMAX + 1, 3):
    POSTS |= {(-48 if (k // 3) % 2 == 0 else -47, k), (47 if (k // 3) % 2 == 0 else 46, k)}
    for xs in CROSS: POSTS.add((xs[(k // 3) % 2], k))
POSTS |= {(XMIN, ZMIN), (XMIN, ZMAX), (XMAX, ZMIN), (XMAX, ZMAX)}
for L in range(2):
    yt = y - BH * (L + 1)
    for c in POSTS:
        add(Part("08_traverse", "3062b", BLACK, ctr(c[0]), yt, ctr(c[1]), 0, {c}, yt, yt + BH))
y -= 2 * BH
t3 = plates("08_traverse", {c: BLACK for c in RING}, y - PH, 1)
t4, nc = bond_layer("08_traverse", RING, t3, y - 2 * PH, BLACK)
TRUSS_TOP = y - 2 * PH


def top_y(cells):
    return min([-BH * HF.get(c, 0) for c in cells] + [0])


SLING_LINKS = SNOT_LINKS

# ---------------- Fliegende Koepfe ----------------
# Dystopische Riesenkoepfe (Stein-Optik, hellgrau) haengen an den Quertraversen; Augen trans-rot (Laser).
# Aufbau von oben: Seil aus runden Steinen -> Schaedel -> Stirn mit Nasenwurzel -> Augen + Nase -> Wangen/Mund
# -> Kinn -> Hals. Alles haengt mit Klemmkraft von oben.
HEADS = []                                                        # entfernt (Nutzerwunsch)                                   # (x, z Mitte, Groesse, Blickrichtung, Seil-Steine)


def head_layers(s):
    """Zellen je Lage relativ zur Mitte (u quer, v = Blickrichtung), von oben nach unten"""
    m = s // 2
    sq = [(u, v) for u in range(-m, m + 1) for v in range(-m, m + 1)]
    inner = [(u, v) for u in range(-m + 1, m) for v in range(-m + 1, m)] or [(0, 0)]
    eyes = [(-max(1, m - 1), m), (max(1, m - 1), m)]
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
            for q in ((-max(1, s_ // 2 - 1), s_ // 2), (max(1, s_ // 2 - 1), s_ // 2)):
                c = cell(q)
                hl = add(Part("09_koepfe", "4070", LBG, ctr(c[0]), yy, ctr(c[1]), ROT_OUT[fwd], {c}, yy, yy + BH, hang=True))
                tx, tz = ctr(c[0]) + fwd[0] * 14, ctr(c[1]) + fwd[1] * 14
                o = (c[0] + fwd[0], c[1] + fwd[1])
                t = add(Part("09_koepfe", "6141", WHITE, tx, yy + 10, tz, 0, {o}, yy, yy + 20, studs=False, hang=True,
                             extra=[f"1 {WHITE} {fmt(tx)} {fmt(yy + 10)} {fmt(tz)} {mat_str(ROT_OUT[fwd])} 6141.dat"]))
                SNOT_LINKS.append((t, hl))
                # Laser: Stange 4L steckt in der Hohlnoppe der Rundplatte (legal), zeigt 15 Grad nach unten ins Publikum
                ca, sa = math.cos(math.radians(35)), math.sin(math.radians(35))
                dx, dz = fwd
                M = [[-dz, dx * ca, -dx * sa], [0, sa, ca], [dx, dz * ca, -dz * sa]]
                bx_, bz_ = ctr(c[0]) + dx * 16, ctr(c[1]) + dz * 16
                add(Part("09_koepfe", "30374", TGREEN, bx_, yy + 10, bz_, 0, set(), yy, yy + 20, studs=False, hang=True,
                         extra=[f"1 {TGREEN} {fmt(bx_)} {fmt(yy + 10)} {fmt(bz_)} " +
                                " ".join(fmt(round(M[i][j], 4)) for i in range(3) for j in range(3)) + " 30374.dat"]))
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
    for z in (-20, -15, -10, 9, 14, 19):
        cells = {(xs[0] + a, z + b) for a in (0, 1) for b in (0, 1)}
        if cells & BUSY or not cells <= RING: continue
        yy = TRUSS_Y
        lens = (TRED, TORANGE, TCLEAR)[len(LIGHTS) % 3]
        for name, col, h in (("3022", BLACK, PH), ("3941", BLACK, BH), ("4032a", lens, PH)):
            add(Part("11_licht", name, col, (xs[0] + 1) * LDU, yy, (z + 1) * LDU, 0, cells, yy, yy + h, hang=True))
            yy += h
        LIGHTS.append((xs[0], z)); BUSY |= cells

# ---------------- PA-Haenge ----------------
# In-the-round: PA an den Laengstraversen ausserhalb des Rings, Lautsprecher zeigen nach aussen zum Publikum
PA = [(x, z) for x in (-26, -9, 9, 26) for z in (-24, 22)]
for ax, az in PA:
    out = -1 if az < 0 else 1
    fz = az if out < 0 else az + 1                                # aeussere Spalte
    bz = fz - out                                                 # innere Spalte
    yy = TRUSS_Y
    add(Part("10_pa", "3022", BLACK, ax * LDU, yy, (az + 1) * LDU, 0, {(ax + a, az + b) for a in (-1, 0) for b in (0, 1)},
             yy, yy + PH, hang=True))
    yy += PH
    for k in range(10):
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
        if k < 9:
            add(Part("10_pa", "3022", BLACK, ax * LDU, yy, (az + 1) * LDU, 0,
                     {(ax + a, az + b) for a in (-1, 0) for b in (0, 1)}, yy, yy + PH, hang=True))
            yy += PH

# ---------------- Minifiguren: Fans und Performer ----------------
def mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mstr(M): return " ".join(fmt(round(v, 4)) for r in M for v in r)
def mv(M, v): return [sum(M[i][k] * v[k] for k in range(3)) for i in range(3)]


def rx(deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[1, 0, 0], [0, c, -s_], [0, s_, c]]


I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


COLORS.update({78: ("Light Nougat", 90), 84: ("Medium Nougat", 150), 92: ("Nougat", 28)})
BL_ID.update({"73200b-f1": "970c00", "98138p07": "98138pb007"})
NAME_OVERRIDE.update({"25412": "Minifig Hair Tousled and Sticking Out on Both Sides"})
SKIN = (78, 84, 92, 70, 308)


def minifig(sub, cells, surf_y, rot, torso, legs, hair=None, arms=(0, 0), head=BLACK, hairpart="3901", mic=False):
    """Minifigur auf den Noppen 'cells' (2 Zellen), Blick nach -z (lokal), arms = Hebewinkel links/rechts"""
    M = RM[rot]
    cx = sum(ctr(c[0]) for c in cells) / 2; cz = sum(ctr(c[1]) for c in cells) / 2
    P = [cx, surf_y - 72, cz]
    comps = [("3626c", head, (0, -24, 0), I3), ("973", torso, (0, 0, 0), I3),
             ("73200b-f1", legs, (0, 32, 0), I3)]
    for sgn, arm, a in ((-1, "3818", arms[0]), (1, "3819", arms[1])):
        A0 = [[0.985, -sgn * 0.174, 0], [sgn * 0.174, 0.985, 0], [0, 0, 1]]
        H0 = [[0.985, -sgn * 0.174, 0], [-sgn * -0.133, 0.754, -0.643], [-sgn * -0.112, 0.633, 0.766]]
        piv = (sgn * 15.552, 9, 0); hand = (sgn * 23.1, 24.7, -10)
        R = rx(a)
        rel = mv(R, [hand[i] - piv[i] for i in range(3)])
        comps.append((arm, torso, piv, mm(R, A0)))
        hp = tuple(piv[i] + rel[i] for i in range(3)); HR = mm(R, H0)
        comps.append(("3820", head, hp, HR))
        if mic and sgn == -1:                                    # Mikrofon im Griffloch der rechten Hand
            o = mv(HR, (0, -6, -10))
            comps.append(("90370", BLACK, tuple(hp[i] + o[i] for i in range(3)), HR))
    if hair is not None: comps.append((hairpart, hair, (0, -24, 0), I3))
    for nm, col, off, Mi in comps:
        w = mv(M, off); pos = [P[0] + w[0], P[1] + w[1], P[2] + w[2]]
        leg = nm == "73200b-f1"
        add(Part(sub, nm, col, pos[0], pos[1], pos[2], rot, set(cells) if leg else set(), surf_y - 96 if leg else 0,
                 surf_y if leg else 0, studs=False,
                 extra=[f"1 {col} {fmt(pos[0])} {fmt(pos[1])} {fmt(pos[2])} {mstr(mm(M, Mi))} {nm}.dat"]))


def remove_tiles(cells):
    """Fliesen ueber 'cells' entfernen und den Rest neu belegen (Figur/Anbau steht auf den Noppen darunter)"""
    for p in [p for p in parts if p.name in TILE.values() and p.cells & cells]:
        parts.remove(p)
        rest = {q: p.color for q in p.cells - cells}
        if rest: plates(p.sub, rest, p.ytop, 0, table=TILE, studs=False)


# Performer oben auf dem Block, Blick den Weg entlang (+x), beide Arme oben
pc = (BLOCK_X[1] - 1, int(math.floor(zc(BLOCK_CX))))                        # vorne an der Blockkante zum Weg
pcells = {pc, (pc[0], pc[1] + 1)}
assert pcells <= (PLAT_CELLS | BRIDGE) and not pcells & PYRO_CELLS, pcells
remove_tiles(pcells)
SUB_NOTES["15_performer"].append(f"0 // FIGUR {fmt(sum(ctr(c[0]) for c in pcells) / 2)} {fmt(-BH * BLOCK_H)} "
                                 f"{fmt(sum(ctr(c[1]) for c in pcells) / 2)} 90")
minifig("15_performer", sorted(pcells), -BH * BLOCK_H, 90, BLACK, DTAN, hair=BLACK, arms=(-115, -160), head=70,
        hairpart="25412", mic=True)        # schwarzes Shirt, helle Cargo-Shorts, wilde Haare

# Fans im Innenraum rundherum, Blick zur Buehne; viele mit erhobenen Armen
TORSOS = [BLACK, BLACK, BLACK, DBG, BLACK, WHITE, BLACK, 288, DBG, BLACK, 308]   # dunkle Konzert-Kleidung
LEGS = [BLACK, BLACK, 272, DBG, BLACK, 272, BLACK]
HAIRS = [BLACK, 308, BLACK, 70, BLACK, None]
FANS = []
fan_used = set()


def crowd_ok(cells):
    for q in cells:
        if not (XMIN + 1 <= q[0] <= XMAX - 1 and ZMIN + 1 <= q[1] <= ZMAX - 1): return False
        for a in range(-2, 3):
            for b in range(-2, 3):
                n = (q[0] + a, q[1] + b)
                if n in HF or n in RESERVED or n in FLOOR_USED: return False
                if abs(a) <= 1 and abs(b) <= 1 and n in fan_used: return False
    return True


k = 0
for x in range(XMIN + 1, XMAX - 1, 3):
    for z in range(ZMIN + 1, ZMAX - 1, 3):
        j = (math.sin(x * 12.9898 + z * 78.233) * 43758.5453) % 1.0
        x0, z0 = x + (1 if j > 0.66 else 0), z + (1 if 0.33 < j <= 0.66 else 0)
        if x0 < SX0 - 8: rot, cells = 90, [(x0, z0), (x0, z0 + 1)]                     # Stirnseite West
        elif x0 > SX1 + 8: rot, cells = 270, [(x0, z0), (x0, z0 + 1)]                  # Stirnseite Ost
        else:
            rot = 0 if z0 > zc(x0 + 1.0) else 180
            cells = [(x0, z0), (x0 + 1, z0)]
        if not crowd_ok(cells): continue
        u = (math.sin(x0 * 3.1 + z0 * 7.7) * 9173.3) % 1.0
        arms = (-165, -165) if u < 0.35 else ((-150, 0) if u < 0.6 else ((0, -140) if u < 0.75 else (0, 0)))
        hsel = int(u * 1000)
        minifig("14_fans", cells, 0, rot, TORSOS[hsel % len(TORSOS)], LEGS[(hsel // 7) % len(LEGS)],
                hair=HAIRS[(hsel // 3) % len(HAIRS)], arms=arms, head=SKIN[(hsel // 11) % len(SKIN)])
        fan_used |= set(cells); FANS.append(cells); k += 1

# Grundplatten
for sx in (-1, 1):
    cells = {(i, k) for i in (range(0, 48) if sx > 0 else range(-48, 0)) for k in range(-24, 24)}
    add(Part("01_baseplates", "4186", BLACK, sx * 480, 0, 0, 0, cells, 0, 4, True))

TITLES = {"01_baseplates": "Grundplatten (2x 48x48)", "02_felsen": "Felswaende und Felsgrate",
          "03_laufweg": "Gewundener Laufweg", "04_plattformen": "Plattform auf dem Block",
          "05_block": "Hoher Felsblock mit Durchgang", "06_gesichter": "Gesichter (SNOT-Augen und -Muender)",
          "07_videoring": "Ovaler Videoring (360 Grad)", "08_traverse": "Tuerme und Traversen-Raster",
          "09_koepfe": "Runde Steinkoepfe mit Gesichtern", "10_pa": "PA-Haenge", "11_licht": "Moving Heads",
          "12_pyro": "Pyro-Flammen und CO2", "13_boden": "Bodenlautsprecher, Uplights, Faesser",
          "14_fans": "Fans (Minifiguren)", "15_performer": "Performer", "16_lift": "Lift im Laufweg (Hubsaeule mit Klappe)"}
print("Buehne:", len(MAT), "Zellen | Koepfe", len(HEADS_R), "| Reliefgesichter", len(RELIEF), "| Felskugeln", len(BOULDERS2),
      "| Spitzen", len(SPIRES), "| Glut", len(EMBERS), "| Felsspots", len(ROCKSPOTS), "| Geroell", len(RUBBLE), "| Treppenstufen", len(STAIR_CELLS), "| Lift bei", LIFT, "| Rillensteine", TEX, "| Ueberhaenge", len(LIPS), "| Augen", len(EYES), "Nasen", len(NOSES), "Muender", len(MOUTHS) + len(SMOUTHS),
      "| Videoring", len(SCREEN), "Zellen,", len(HANGERS), "Seile | Scheinwerfer", len(LIGHTS),
      "| Pyro", len(PYRO), "| Subs", len(SUBS), "| Uplights", len(UPLIGHTS), "| Monitore", len(MONITORS), "| Fans", len(FANS))


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
    ground = {n for n, p in enumerate(parts) if p.name in ("3811", "4186")}
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
    floating = [n for n in phys if parts[n].name not in ("3811", "4186") and not below[n] and not parts[n].hang]
    hanging_ok = [n for n in phys if not below[n] and parts[n].hang and above[n]]
    # Zell-Unterstuetzung (streng) nur als Info
    unsup_cells = 0
    for n in phys:
        p = parts[n]
        if p.name in ("3811", "4186") or p.hang: continue
        for c in p.cells:
            if not idx_top.get((p.ybot, c)): unsup_cells += 1
    # Kollisionen (8-LDU-Slabs)
    occ = {}; coll = []
    for n in phys:
        p = parts[n]
        if p.name in ("3811", "4186"): continue
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
    names.update(NAME_OVERRIDE)
    order = sorted({p.sub for p in parts})
    bysub = defaultdict(list)
    for p in parts: bysub[p.sub] += p.lines()
    out = [f"0 FILE {NAME}.ldr", "0 Travis Scott - Circus Maximus (UTOPIA) Stage (LEGO MOC)", f"0 Name: {NAME}.ldr",
           "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""]
    for s in order: out += [f"0 // {TITLES.get(s, s)}", f"1 16 0 0 0 {ROT[0]} {s}.ldr"]
    out += ["0 NOFILE"]
    for s in order:
        out += [f"0 FILE {s}.ldr", f"0 {TITLES.get(s, s)}", f"0 Name: {s}.ldr"] + SUB_NOTES.get(s, []) + bysub[s] + ["0 NOFILE"]
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
