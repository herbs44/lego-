"""
Yeezus Stage – LEGO MOC Generator
Mount Yeezus (Fels-Berg mit Spitze und Simsen), Buehnenpodest, Laufsteg mit Rampe, Lower Stage (Felsplateau),
runder Screen, Traverse mit Line-Arrays und Moving Heads. Massstab: 2 Baseplates 32x32.
Pipeline: Hoehenfeld -> Schale + Stuetz-Propagation -> Slopes an Stufenkanten -> Packing -> Checks -> MPD/BOM/XML
"""
import math, random, os, sys
from collections import defaultdict, Counter

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
NAME = "yeezus_stage"
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
#                                  YEEZUS STAGE
# =====================================================================================
# Koordinaten: Zellen x in [-32, 31], z in [-16, 15] (2 Baseplates 32x32 nebeneinander).
# Vorne = +z (Publikum). Von vorne gesehen liegt +x LINKS: der Berg steht bei +x (links, wie in
# den Ansichtszeichnungen), die Lower Stage bei -x (rechts).
COLORS.update({212: ("Bright Light Blue", 105), 25: ("Orange", 4)})
XMIN, XMAX, ZMIN, ZMAX = -32, 31, -16, 15
GRID = [(i, k) for i in range(XMIN, XMAX + 1) for k in range(ZMIN, ZMAX + 1)]
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ROT_OUT = {(1, 0): 90, (-1, 0): 270, (0, 1): 180, (0, -1): 0}    # Slope-Gefaelle (Standard: nach -z)
rng = random.Random(11)

# ---------------- Hoehenfeld (in Steinhoehen) ----------------
PLAT = {(i, k) for i in range(8, 30) for k in range(-10, 11)}          # Buehnenpodest unter dem Berg
PLAT_H = 3
RUNWAY = {(i, k) for i in range(-11, 8) for k in range(-2, 3)}          # Laufsteg
RUNWAY_H = 2
RAMP = {(i, k) for i in range(-13, -11) for k in range(-2, 3)}          # Rampe zur Lower Stage
STAIR = {(i, 3) for i in range(-3, 0)}                                  # Treppenstufe vorne am Laufsteg
STAGE_C, STAGE_R = (-22.0, 0.0), 8.6                                    # Lower Stage (Felsplateau)
STAGE_H = 4
APEX = (17.0, -1.0); APEX_H = 19


def planes_height(p, apex, h0, faces):
    """konvexes Polyeder: h0 - max_i s_i * ((p - apex) . n_i)"""
    x, z = p
    m = max(s * ((x - apex[0]) * math.cos(math.radians(t)) + (z - apex[1]) * math.sin(math.radians(t)))
            for t, s in faces)
    return h0 - max(0.0, m)


# Berg: Spitze (Pyramide) + drei Felsmassen als Unterbau (Simse fuer den Chor)
PEAK = dict(apex=APEX, h0=APEX_H + 0.4, faces=[(78, 1.30), (168, 1.05), (262, 1.35), (352, 1.15), (215, 1.2)])
MASSES = [dict(apex=(20.0, 1.5), h0=12.0, cap=9.0, faces=[(95, 2.3), (185, 1.5), (272, 2.0), (5, 1.9), (140, 1.8)]),
          dict(apex=(11.5, 3.0), h0=8.5, cap=6.0, faces=[(90, 2.2), (180, 2.6), (270, 1.6), (0, 1.2)]),
          dict(apex=(25.0, -5.0), h0=11.0, cap=8.0, faces=[(80, 1.7), (175, 1.4), (265, 2.2), (355, 2.4)])]
CRACKS = [[(17.0, -1.0), (17.6, 3.0), (16.4, 6.0), (17.2, 9.5)],          # Riss vorne durch die Spitze
          [(20.5, 3.5), (23.0, 6.5), (22.2, 9.8)],
          [(13.0, 2.5), (11.0, 6.0)]]


def seg_dist(p, a, b):
    ax, az = a; bx, bz = b; px, pz = p
    dx, dz = bx - ax, bz - az; L = dx * dx + dz * dz
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L)) if L else 0.0
    return math.hypot(px - ax - t * dx, pz - az - t * dz)


def crack_d(p, cracks=CRACKS):
    return min(seg_dist(p, a, b) for poly in cracks for a, b in zip(poly, poly[1:]))


def mountain_f(p):
    """kontinuierliche Berghoehe (Steine) ueber dem Podest"""
    h = planes_height(p, PEAK["apex"], PEAK["h0"], PEAK["faces"])
    for m in MASSES:
        h = max(h, min(m["cap"], planes_height(p, m["apex"], m["h0"], m["faces"])))
    return h


def stage_f(p):
    """Lower Stage: Felsplateau mit unregelmaessigem Rand und steilen Felswaenden"""
    x, z = p[0] - STAGE_C[0], p[1] - STAGE_C[1]
    a = math.atan2(z, x)
    r = STAGE_R * (1 + 0.10 * math.sin(3 * a + 0.7) + 0.06 * math.sin(7 * a + 2.1) + 0.04 * math.sin(11 * a))
    r_x = r * 1.12                                             # etwas laenger als breit
    d = math.hypot(x / 1.12, z) * 1.12 / (r_x / r) if r else 0
    edge = r - math.hypot(x, z * 1.08)
    return STAGE_H * max(0.0, min(1.0, 0.25 + edge / 2.2))


TOWERS = [(31, -1), (31, 1), (-31, -1), (-31, 1)]   # je 2 Gittertraeger nebeneinander (Tiefe der Traverse)
RESERVED = {(X + a, Z + b) for X, Z in TOWERS for a in (-1, 0) for b in (-1, 0)}
HF, MAT = {}, {}
for c in GRID:
    if c in RESERVED: continue
    p = (c[0] + 0.5, c[1] + 0.5)
    h, m = 0, None
    if c in PLAT:
        h, m = PLAT_H, "podest"
        if 9 <= c[0] <= 28 and -9 <= c[1] <= 9:
            hm = mountain_f(p)
            if crack_d(p) < 0.5: hm -= 1.0                     # Risse als Kerben
            if hm >= PLAT_H + 0.5:
                h, m = max(PLAT_H, int(round(hm))), "berg"
    elif c in RUNWAY: h, m = RUNWAY_H, "laufsteg"
    elif c in RAMP: h, m = (3 if c[0] == -12 else 4), "rampe"
    elif c in STAIR: h, m = 1, "laufsteg"
    else:
        hs = stage_f(p)
        if hs > 0.5: h, m = int(round(hs)), "fels"
    if h: HF[c], MAT[c] = h, m
# Gipfelplattform 2x2
for c in ((16, -2), (17, -2), (16, -1), (17, -1)): HF[c], MAT[c] = APEX_H, "berg"
GMAX = max(HF.values())
S = [{c for c, h in HF.items() if h > g} for g in range(GMAX + 1)]


def grad_dirs(c):
    """Richtungen nach Gefaelle sortiert (staerkstes Gefaelle zuerst)"""
    p = (c[0] + 0.5, c[1] + 0.5)
    f = mountain_f if MAT.get(c) in ("berg", "podest") else stage_f
    g = [(f((p[0] + d[0] * 0.7, p[1] + d[1] * 0.7)) - f(p), d) for d in DIRS]
    g.sort()
    return [d for _, d in g]


# ---------------- Rock-Farben ----------------
def vnoise(x, z, sc=3.0, seed=0):
    """glatte Werte-Rauschfunktion 0..1"""
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx
    b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


SUN = (0.35, 0.8, 0.9)   # Licht von vorne-oben (etwas von links)
def rock_color(c, top=False):
    if MAT.get(c) == "berg" and crack_d((c[0] + 0.5, c[1] + 0.5)) < 0.75: return DBG
    if MAT.get(c) == "fels" and crack_d((c[0] + 0.5, c[1] + 0.5), STAGE_CRACKS) < 0.6: return DBG
    if top:
        v = vnoise(c[0] + 0.5, c[1] + 0.5, 3.2, 1 if MAT.get(c) == "fels" else 2)
        if MAT.get(c) == "fels": return WHITE if v > 0.62 else LBG
        return LBG if v > 0.68 else WHITE
    p = (c[0] + 0.5, c[1] + 0.5)
    f = mountain_f if MAT.get(c) == "berg" else stage_f
    gx = f((p[0] + 0.5, p[1])) - f((p[0] - 0.5, p[1])); gz = f((p[0], p[1] + 0.5)) - f((p[0], p[1] - 0.5))
    n = (-gx, 1.0, -gz); L = math.sqrt(sum(v * v for v in n))
    shade = sum(a * b for a, b in zip(n, SUN)) / L
    shade -= 0.3 * (vnoise(c[0] + 0.5, c[1] + 0.5, 2.5, 3) > 0.72)
    return WHITE if shade > 0.55 else LBG


STAGE_CRACKS = [[(-28.0, -3.0), (-24.0, -1.0), (-21.0, 2.5), (-17.0, 3.0)],
                [(-24.0, -1.0), (-23.0, -5.5)], [(-19.0, -6.0), (-16.5, -2.0)]]
ROCK = ("berg", "fels")
SLOPE_OK = ("berg", "fels", "rampe")

# ---------------- Schale, Decks und Stuetzen ----------------
def chebyshev_dist(Sg):
    """Abstand (in Zellen) jeder Zelle zum Rand der Menge (BFS, 8er-Nachbarschaft)"""
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
    deck[g] = {c for c in exposed if dist[c] > T_SHELL + 1 and MAT[c] != "laufsteg"}
    solid[g] = {c for c in Sg if dist[c] <= T_SHELL or c in exposed} - deck[g]
    for c in deck[g]:
        if c[0] % 4 == 0 and c[1] % 4 == 0:
            blk = {(c[0] + a, c[1] + b) for a in (0, 1) for b in (0, 1)}
            if blk <= deck[g]: pillars[g] |= blk
for g in range(GMAX, 0, -1):          # Stuetz-Propagation: alles braucht etwas darunter
    solid[g - 1] |= solid[g] | pillars[g]
    deck[g - 1] -= solid[g - 1]

# ---------------- Rundung: Slopes an Stufenkanten ----------------
STEP_PART = {1: "3040b", 2: "4286", 3: "60477"}          # 45 / 33 / 18 Grad, Hoehe 1 Stein
STEEP_PART = {2: "60481", 3: "4460b"}                    # 65 / 75 Grad, Hoehe 2 / 3 Steine
replaced = set()     # (Zelle, Lage) - Stein durch Slope ersetzt
covered = set()      # (Zelle, Lage) - von Slope-Schraege belegt
SLOPES = []          # (Teil, Zelle, Richtung, Lage unten, Hoehe, Zellen)
for g in range(0, GMAX + 1):
    for c in sorted(S[g]):
        if MAT[c] not in SLOPE_OK or (c, g) in replaced or c not in solid[g]: continue
        for d in grad_dirs(c):
            n = (c[0] + d[0], c[1] + d[1])
            if n in S[g]: continue
            below = S[g - 1] if g > 0 else ({q for q in GRID} if MAT[c] == "fels" else set())
            if n not in below or (n, g) in covered: continue
            if MAT.get(n) not in SLOPE_OK + ("podest", "laufsteg", None): continue
            run, q = [], n
            while q in below and q not in S[g] and (q, g) not in covered and len(run) < 3 and q not in RESERVED \
                    and XMIN <= q[0] <= XMAX and ZMIN <= q[1] <= ZMAX:
                run.append(q); q = (q[0] + d[0], q[1] + d[1])
            if not run: continue
            if g == 0: run = run[:1]                          # am Boden keine langen Zungen
            h = 1
            while h < 3 and g + h <= GMAX and c in S[g + h] and (c, g + h) not in replaced and c in solid[g + h]:
                h += 1
            if h >= 2:
                name, cells, layers = STEEP_PART[h], [c, n], range(g, g + h)
            else:
                name, cells, layers = STEP_PART[len(run)], [c] + run, [g]
            SLOPES.append((name, c, d, g, len(layers), cells))
            for L in layers:
                replaced.add((c, L))
                for q in cells[1:]: covered.add((q, L))
            break

# ---------------- Bauen: Lagen ----------------
def side_visible(c, g):
    return any((c[0] + a, c[1] + b) not in S[g] for a, b in DIRS)


def body_color(c, g):
    m = MAT[c]
    if m in ROCK:
        vis = side_visible(c, g) or c not in (S[g + 1] if g + 1 <= GMAX else set())
        return rock_color(c) if vis else BLACK
    if m == "rampe": return BLACK
    # Podest / Laufsteg: schwarz, sichtbare Fugen dunkelgrau (Paneele)
    return BLACK


def sub_of(c):
    return {"podest": "02_podest", "berg": "03_berg", "laufsteg": "04_laufsteg", "rampe": "04_laufsteg",
            "fels": "05_lower_stage"}[MAT[c]]


for g in range(GMAX + 1):
    cells = {c for c in solid[g] if (c, g) not in replaced}
    bysub = defaultdict(dict)
    for c in cells: bysub[sub_of(c)][c] = body_color(c, g)
    for sb, cc in bysub.items(): bricks(sb, cc, g)
    # Decks (3 Plattenlagen) auf Pfeilern
    if deck[g]:
        y0 = -BH * g
        by = defaultdict(set)
        for c in deck[g]: by[sub_of(c)].add(c)
        for sb, dc in by.items():
            l1 = plates(sb, {c: BLACK for c in dc}, y0 - PH, 0)
            sup = solid[g - 1] if g > 0 else set(GRID)
            for p in l1:
                if not (p.cells & sup): p.hang = True
            l2, nc = bond_layer(sb, dc, l1, y0 - 2 * PH, BLACK)
            plates(sb, {c: BLACK for c in dc}, y0 - 3 * PH, 1)

for (name, c, d, g, h, cells) in SLOPES:
    y = -BH * (g + h)
    col = rock_color(c) if MAT[c] in ROCK else BLACK
    add(Part(sub_of(c), name, col, ctr(c[0]), y, ctr(c[1]), ROT_OUT[d], cells, y, y + BH * h,
             studs=True, studcells={c}))

# Abdeckung aller noch offenen Oberseiten: Cheese-Slopes an Felskanten, sonst Fliesen
caps = defaultdict(dict)
SUMMIT = {(16, -2), (17, -2), (16, -1), (17, -1)}
for g in range(GMAX + 1):
    Sa = S[g + 1] if g + 1 <= GMAX else set()
    y = -BH * (g + 1)
    for c in S[g] - Sa:
        if (c, g + 1) in covered or (c, g) in replaced: continue
        m = MAT[c]
        if c in SUMMIT: caps[(g, "03_berg")][c] = BLACK; continue
        if m in ROCK:
            drop = [d for d in grad_dirs(c) if (c[0] + d[0], c[1] + d[1]) not in S[g]]
            if drop and rng.random() < 0.8:
                add(Part(sub_of(c), "54200", rock_color(c, top=True), ctr(c[0]), y, ctr(c[1]), ROT_OUT[drop[0]],
                         {c}, y - 16, y, studs=False))
                continue
            caps[(g, sub_of(c))][c] = rock_color(c, top=True)
        elif m == "rampe": caps[(g, sub_of(c))][c] = DBG
        elif m == "podest":
            edge = any((c[0] + a, c[1] + b) not in S[g] for a, b in DIRS)
            caps[(g, sub_of(c))][c] = DBG if edge else BLACK
        else: caps[(g, sub_of(c))][c] = DBG
for (g, sb), cc in caps.items():
    plates(sb, cc, -BH * (g + 1) - PH, g % 2, table=TILE, studs=False)

# ---------------- Runder Screen hinter dem Berg ----------------
DISC_C, DISC_R, DISC_ROW0 = (18.5, 17.0), 13.0, 6
DISC_Z = [-16, -15, -14, -13]


def disc_cells(r):
    dy = (r + 0.5 - DISC_C[1]) * 1.2
    if abs(dy) > DISC_R: return []
    hw = math.sqrt(DISC_R ** 2 - dy * dy)
    return [x for x in range(XMIN, XMAX + 1) if abs(x + 0.5 - DISC_C[0]) <= hw]


def sky(x, r):
    """Himmel wie auf dem Foto: tiefes Blau oben, grosse weisse Wolkenbaenke, gleissendes Licht
    unten rechts (von vorne gesehen rechts = kleines x)"""
    t = (r + 0.5 - (DISC_C[1] - DISC_R / 1.2)) / (2 * DISC_R / 1.2)       # 0 unten .. 1 oben
    u = x + 0.5 - DISC_C[0]                                                 # >0 = links von vorne
    glow = math.hypot((u + 7.5) / 1.3, (t - 0.28) * 24)
    if glow < 3.2: return WHITE
    cloud = (math.sin(0.42 * u + 0.9 * t * 6 + 1.1) + 0.7 * math.sin(0.8 * u - 1.7 * t * 6 + 0.3)
             + 0.6 * math.sin(0.23 * u + 2.9) - 1.4 * t + 0.5) / 2.2
    if glow < 5.5 and cloud > -0.3: return WHITE
    if cloud > 0.38: return WHITE
    if cloud > 0.22: return LBG if t > 0.45 else 212
    if t > 0.72: return BLUE
    if t > 0.4: return MBLUE
    return 212


DISC_ROWS = {}
r = DISC_ROW0
while True:
    xs = disc_cells(r)
    if not xs and r > DISC_C[1]: break
    if xs: DISC_ROWS[r] = xs
    r += 1
PED_X = range(12, 26)
for g in range(DISC_ROW0):                                     # Sockel
    bricks("07_screen", {(x, z): BLACK for x in PED_X for z in DISC_Z}, g)
SIZES = [1, 2, 3, 4, 6, 8]


def partition(L, left_need, right_need, prev_joints):
    """Lauf der Laenge L in Steinlaengen zerlegen: Endsteine reichen auf gestuetzte Zellen,
    Fugen moeglichst versetzt zur Lage darunter (Verband)"""
    INF = 10 ** 9
    best = [INF] * (L + 1); back = [None] * (L + 1); best[0] = 0
    for pos in range(L):
        if best[pos] == INF: continue
        for s in SIZES:
            e = pos + s
            if e > L: continue
            if pos == 0 and s < left_need: continue
            if e == L and s < right_need: continue
            cost = best[pos] + 1 + (3 if e < L and e in prev_joints else 0)
            if cost < best[e]: best[e] = cost; back[e] = pos
    out, e = [], L
    while e > 0: out.append(e - back[e]); e = back[e]
    return out[::-1]


prev = {band: (set(PED_X), set()) for band in ("a", "b", "c", "d", "e")}
prev_cells = set(PED_X); prev_j = defaultdict(set)
for r, xs in sorted(DISC_ROWS.items()):
    # hinten eine schwarze Rueckwand (1 Noppe), davor 3 Noppen Bild; Fugen im Verband
    bands = [(-16,), (-15, -14), (-13,)] if r % 2 == 0 else [(-16,), (-15,), (-14, -13)]
    joints_here = set()
    for band in bands:
        run = list(xs); sup = [x for x in run if x in prev_cells]
        left_need = (sup[0] - run[0] + 1) if sup else 1
        right_need = (run[-1] - sup[-1] + 1) if sup else 1
        pj = {x - run[0] for x in prev_j[min(band)] | prev_j[max(band)]}
        pos = 0
        for s_ in partition(len(run), left_need, right_need, pj):
            seg = run[pos:pos + s_]; pos += s_
            joints_here.add(seg[-1] + 1)
            col = BLACK if -16 in band and len(band) == 1 else Counter(sky(x, r) for x in seg).most_common(1)[0][0]
            w = len(band)
            key = (min(w, s_), max(w, s_))
            cells = [(x, z) for x in seg for z in band]
            cx = sum(ctr(q[0]) for q in cells) / len(cells); cz = sum(ctr(q[1]) for q in cells) / len(cells)
            add(Part("07_screen", BRICK[key], col, cx, -BH * (r + 1), cz, 0 if s_ >= w else 90,
                     cells, -BH * (r + 1), -BH * r))
        for z in band: prev_j[z] = {j_ for j_ in joints_here}
    prev_cells = set(xs)

# ---------------- Tuerme und Traverse ----------------
TRUSS_Y = -BH * 3 - 3 * 240 - 2 * PH       # Unterkante Traverse (= Oberkante Tuerme)
for sx in (-1, 1):
    # Sockel 2x4 im Verband (2 Steine), darauf je Turm 2 Gittertraeger nebeneinander mit Platte 2x4 dazwischen
    base = {(X + a, Z + b) for X, Z in TOWERS if (X > 0) == (sx > 0) for a in (-1, 0) for b in (-1, 0)}
    for g in range(3):
        pack("08_traverse", {c: BLACK for c in base}, BRICK, -BH * (g + 1), BH, g % 2)
    yy = -BH * 3
    for k in range(3):
        yy -= 240
        for X, Z in TOWERS:
            if (X > 0) != (sx > 0): continue
            cells = {(X - 1, Z - 1), (X, Z - 1), (X - 1, Z), (X, Z)}
            add(Part("08_traverse", "95347", LBG, X * LDU, yy, Z * LDU, 0 if X < 0 else 180, cells, yy, yy + 240))
        if k < 2:
            yy -= PH
            plates("08_traverse", {c: LBG for c in base}, yy, 1)
assert yy == TRUSS_Y + 2 * PH - 2 * PH, (yy, TRUSS_Y)
TR = {(i, k) for i in range(XMIN, XMAX + 1) for k in range(-2, 2)}   # 4 breit, ueber die ganze Laenge
y = TRUSS_Y - PH
t1 = plates("08_traverse", {c: LBG for c in TR}, y, 0)
for p in t1:
    if not any(c in {(X - 1, Z - 1), (X, Z - 1), (X - 1, Z), (X, Z)} for (X, Z) in TOWERS for c in p.cells): p.hang = True
t2, nc = bond_layer("08_traverse", TR, t1, y - PH, LBG)
assert nc == 1
y -= PH
POSTS = {(i, -2 if (i - XMIN) % 6 == 0 else 1) for i in range(XMIN, XMAX + 1, 3)} | \
        {(i, 1 if (i - XMIN) % 6 == 0 else -2) for i in range(XMIN + 1, XMAX + 1, 3)} | \
        {(XMIN, 1), (XMAX, -2), (XMAX, 1)}
for L in range(2):
    yt = y - BH * (L + 1)
    for c in POSTS:
        add(Part("08_traverse", "3062b", LBG, ctr(c[0]), yt, ctr(c[1]), 0, {c}, yt, yt + BH))
y -= 2 * BH
t3 = plates("08_traverse", {c: LBG for c in TR}, y - PH, 1)
t4, nc = bond_layer("08_traverse", TR, t3, y - 2 * PH, LBG)
TRUSS_TOP = y - 2 * PH

# Line-Arrays: 8 Boxen (Stein 2x3 schwarz + Platte 2x3 dunkelgrau), J-Kurve nach vorne
ARRAYS_X = [27, 23, 11, 7]                 # Gitterpunkt (Mitte 2x2) ueber den Bergflanken
def top_y(cells):
    return min([-BH * HF.get(c, 0) for c in cells] + [0])
for ax in ARRAYS_X:
    # so viele Boxen, dass unten mind. 2 Steine Luft zur Bergoberflaeche bleiben
    J_OFF = [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4]
    while True:
        yy = TRUSS_Y + PH; ok = True
        for k, off in enumerate(J_OFF):
            cz = {(ax + a, -1 + off + b) for a in (-1, 0) for b in (0, 1)}
            yy += BH + (PH if k < len(J_OFF) - 1 else 0)
            if yy > top_y(cz) - 2 * BH: ok = False; break
        if ok: break
        J_OFF = J_OFF[:3] + J_OFF[4:]            # eine gerade Box weniger, Kurve bleibt

    yy = TRUSS_Y
    add(Part("09_line_arrays", "3022", DBG, ax * LDU, yy, 0, 0, {(ax - 1, -1), (ax, -1), (ax - 1, 0), (ax, 0)},
             yy, yy + PH, hang=True))                      # Aufhaengung (Rigging-Rahmen)
    yy += PH
    for k, off in enumerate(J_OFF):
        z0 = -1 + off
        cells = {(ax + a, z0 + b) for a in (-1, 0) for b in (0, 1)}
        add(Part("09_line_arrays", "3003", BLACK, ax * LDU, yy, (z0 + 1) * LDU, 0, cells, yy, yy + BH, hang=True))
        yy += BH
        if k < len(J_OFF) - 1:
            nz = -1 + J_OFF[k + 1]
            pc = {(ax + a, nz + b) for a in (-1, 0) for b in (0, 1)}
            add(Part("09_line_arrays", "3022", DBG, ax * LDU, yy, (nz + 1) * LDU, 0, pc, yy, yy + PH, hang=True))
            yy += PH

# Moving Heads ueber der Lower Stage
HEADS_X = [-29, -25, -21, -17, -13]
for hx in HEADS_X:
    cells = {(hx + a, -1 + b) for a in (0, 1) for b in (0, 1)}
    yy = TRUSS_Y
    for name, col, h in (("3022", BLACK, PH), ("3941", BLACK, BH), ("4032a", TCLEAR, PH)):
        add(Part("10_licht", name, col, (hx + 1) * LDU, yy, 0, 0, cells, yy, yy + h, hang=True))
        yy += h

# Grundplatten
for sx in (-1, 1):
    cells = {(i, k) for i in (range(0, 32) if sx > 0 else range(-32, 0)) for k in range(-16, 16)}
    add(Part("01_baseplates", "3811", BLACK, sx * 320, 0, 0, 0, cells, 0, 4, True))

SLING_LINKS = []
TITLES = {"01_baseplates": "Grundplatten (2x 32x32)", "02_podest": "Buehnenpodest", "03_berg": "Mount Yeezus",
          "04_laufsteg": "Laufsteg mit Rampe", "05_lower_stage": "Lower Stage (Felsplateau)",
          "07_screen": "Runder Screen", "08_traverse": "Tuerme und Traverse", "09_line_arrays": "Line-Arrays",
          "10_licht": "Moving Heads"}


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
    out = [f"0 FILE {NAME}.ldr", "0 Yeezus Stage - Mount Yeezus (LEGO MOC)", f"0 Name: {NAME}.ldr",
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
