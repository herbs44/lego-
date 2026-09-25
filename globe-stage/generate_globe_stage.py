"""
Globe Stage – LEGO MOC Generator
Konzertbuehne mit Erdkugel-Kuppel, Lichtvorhang, Projektionsschirm und Truss-Ring.
Pipeline: Zellgeometrie -> Farben -> Packing (Rechteck-Merge) -> Statik-/Kollisionscheck -> MPD/BOM/XML
"""
import math, random, os, sys
from collections import defaultdict, Counter

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
NAME = "globe_stage"
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
          308: ("Dark Brown", 120), 272: ("Dark Blue", 63), 288: ("Dark Green", 80)}

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
TECHNIC = {(1, 1): "6541", (1, 2): "3700", (1, 4): "3701", (1, 6): "3894", (1, 8): "3702"}
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "6141": "4073", "3815c01": "970c00"}


class Part:
    __slots__ = ("sub", "name", "color", "x", "y", "z", "rot", "cells", "ytop", "ybot", "studs", "hang", "extra")

    def __init__(s, sub, name, color, x, y, z, rot, cells, ytop, ybot, studs=True, hang=False, extra=None):
        s.sub, s.name, s.color, s.x, s.y, s.z, s.rot = sub, name, color, x, y, z, rot
        s.cells, s.ytop, s.ybot, s.studs, s.hang, s.extra = frozenset(cells), ytop, ybot, studs, hang, extra

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
def split_run(L):
    if L in SIZES1: return [L]
    for a in sorted(SIZES1, reverse=True):
        if (L - a) in SIZES1: return [a, L - a]
    out = []
    while L > 0:
        a = max(x for x in SIZES1 if x <= L); out.append(a); L -= a
    return out


def place_runs(sub, runs, color, ytop, table=PLATE, height=PH, hang=False, studs=True):
    res = []
    for run in runs:
        pos = 0
        for n in split_run(len(run)):
            seg = run[pos:pos + n]; pos += n
            xs = {c[0] for c in seg}
            cx = sum(ctr(c[0]) for c in seg) / n; cz = sum(ctr(c[1]) for c in seg) / n
            rot = 0 if len(xs) >= len({c[1] for c in seg}) else 90
            res.append(add(Part(sub, table[(1, n)], color, cx, ytop, cz, rot, seg, ytop, ytop + height, studs, hang)))
    return res


# ---------------- Erd-Textur (orthografische Draufsicht) ----------------
from global_land_mask import globe
LAT0, LON0 = math.radians(32), math.radians(16)
R_DOME = 24.0
CLOUD_PHASE = (1.402, 4.073, 2.480)


def earth_color(c):
    u = (c[0] + 0.5) / R_DOME * 0.985
    n = -(c[1] + 0.5) / R_DOME * 0.985
    rho = math.hypot(u, n)
    if rho >= 1: rho = 0.9999; u, n = u / math.hypot(u, n) * rho, n / math.hypot(u, n) * rho
    if rho < 1e-9: lat, lon = LAT0, LON0
    else:
        cc = math.asin(rho)
        lat = math.asin(math.cos(cc) * math.sin(LAT0) + n * math.sin(cc) * math.cos(LAT0) / rho)
        lon = LON0 + math.atan2(u * math.sin(cc), rho * math.cos(cc) * math.cos(LAT0) - n * math.sin(cc) * math.sin(LAT0))
    la, lo = math.degrees(lat), (math.degrees(lon) + 180) % 360 - 180
    # Wolken (prozedural, Wirbel)
    X, Y, Z = math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)
    p = CLOUD_PHASE   # per Suche gewaehlt: ~13% Wolken, Frontseite frei, Land kaum verdeckt
    f = (math.sin(4.1 * X + p[0] + 2.3 * math.sin(3.3 * Z + 1.1)) * math.cos(3.7 * Y + p[1] - 1.9 * math.sin(2.9 * X))
         + 0.6 * math.sin(6.3 * Z + 2.7 * Y + p[2] + 1.3 * math.sin(5.1 * X)))
    if la > 72 or la < -80: return WHITE
    if f > 0.62: return WHITE
    land = bool(globe.is_land(la, lo))
    if not land: return BLUE
    desert = ((12 < la < 34 and -18 < lo < 60) or (-30 < la < -18 and 115 < lo < 145) or
              (-28 < la < -17 and 14 < lo < 26) or (24 < la < 40 and 60 < lo < 75))
    steppe = (35 <= la < 50 and 45 < lo < 110) or (25 < la < 38 and -118 < lo < -100)
    if desert: return TAN
    if steppe: return DTAN
    return GREEN


# ---------------- Geometrie ----------------
G_T0, G_T1, G_LED, G_DOME = 0, 2, 4, 6
N_DOME = 14
def r_dome(n): return R_DOME * math.sqrt(max(0.0, 1 - ((n + 0.5) * 24 / (N_DOME * 24 + 6.0)) ** 2)) - 0.4


layers = {}           # g -> set of cells (Brick-Lagen inkl. Deck-Lagen)
full = {}             # g -> volle Scheibe (ohne Hohlraum) fuer Sichtbarkeit
D_T0, D_T1, D_LED = disk(31.5), disk(27.5), disk(25.5)
DOME = [disk(r_dome(n)) for n in range(N_DOME)]
DECKS = {7: None, 11: None}  # Dome-Lagen, die als Plattendeck ausgefuehrt werden
SEG_INNER = [(0, 6, 16.0), (8, 10, 11.0)]  # (dome n von, bis, Innenradius Hohlraum)


def inner_for_g(g):
    n = g - G_DOME
    if g < G_DOME: return 16.0
    for a, b, r in SEG_INNER:
        if a <= n <= b: return r
    return None  # massiv (Top-Segment) bzw. Deck


for g in range(0, G_DOME + N_DOME):
    if g < 2: S = D_T0
    elif g < 4: S = D_T1
    elif g < 6: S = D_LED
    else: S = DOME[g - G_DOME]
    full[g] = S
    A = inner_for_g(g)
    if A is not None and (g - G_DOME) not in DECKS:
        S = {c for c in S if dist(c) >= A}
    layers[g] = S

TOP_G = G_DOME + N_DOME - 1


def outer_r(g):
    if g < 2: return 31.5
    if g < 4: return 27.5
    if g < 6: return 25.5
    return r_dome(g - G_DOME)


def covered_above(g, c):
    return (g + 1) in full and c in full[g + 1]


def color_of(g, c):
    d = dist(c); R = outer_r(g)
    band = d > R - 1.5
    exposed = not covered_above(g, c)
    if g < 2: return BLACK
    if g < 4: return DBG if band else BLACK
    if g == 4: return WHITE if (d > R - 2.0 or exposed) else BLACK
    if g == 5:
        if c in boundary8(D_LED): return TCLEAR
        return WHITE if (d > R - 2.5 or exposed) else BLACK
    return earth_color(c) if (band or exposed) else BLACK


B8_LED = boundary8(D_LED)

# ---- Basis-Grundplatten ----
for sx in (-1, 1):
    for sz in (-1, 1):
        cells = {(i, k) for i in (range(0, 32) if sx > 0 else range(-32, 0)) for k in (range(0, 32) if sz > 0 else range(-32, 0))}
        add(Part("01_baseplates", "3811", BLACK, sx * 320, 0, sz * 320, 0, cells, 0, 4, True))

SUBNAME = {}
def sub_for_g(g):
    if g < 2: return "02_basis"
    if g < 4: return "03_laufsteg"
    if g < 6: return "04_led_ring"
    n = g - G_DOME
    if n <= 6: return "05_kuppel_unten"
    if n <= 11: return "06_kuppel_mitte"
    return "07_kuppel_oben"


# ---- Brick-Lagen ----
DECK_BOTTOM = {}
for g in range(0, TOP_G + 1):
    n = g - G_DOME
    S = layers[g]
    sub = sub_for_g(g)
    if n in DECKS:
        # Deck: Aussenring als Bricks (sichtbar, Erdfarben), Innenscheibe als 3 Plattenlagen
        R = outer_r(g)
        ring = {c for c in S if dist(c) > R - 2.0 or not covered_above(g, c)}
        disc = S - ring
        bricks(sub, {c: color_of(g, c) for c in ring}, g)
        y0 = -BH * g
        for s in range(3):
            ps = plates(sub, {c: BLACK for c in disc}, y0 - PH * (s + 1), s % 2)
            if s == 0: DECK_BOTTOM[n] = ps
    else:
        bricks(sub, {c: color_of(g, c) for c in S}, g)

# ---- Stuetzen in den Hohlraeumen (werden fuer unsupported Deck-Platten ergaenzt) ----
def pillar_stack(sub, cells, g_from, g_to, color=BLACK):
    for g in range(g_from, g_to + 1):
        cc = {c: color for c in cells}
        pack(sub, cc, BRICK, -BH * (g + 1), BH, g % 2)


PILLAR_GRID = {0: [(-8, -8), (-8, 0), (-8, 8), (0, -8), (0, 0), (0, 8), (8, -8), (8, 0), (8, 8)],
               1: [(-4, -4), (4, 4), (-4, 4), (4, -4)]}
def pillar_cells(gx, gz): return {(gx - 1, gz - 1), (gx, gz - 1), (gx - 1, gz), (gx, gz)}

for (gx, gz) in PILLAR_GRID[0]:
    pillar_stack("08_innenstuetzen", pillar_cells(gx, gz), 0, G_DOME + 7 - 1)
for (gx, gz) in PILLAR_GRID[1]:
    pillar_stack("08_innenstuetzen", pillar_cells(gx, gz), G_DOME + 8, G_DOME + 11 - 1)

def top_index():
    return {(p.ytop, c) for p in parts if p.studs for c in p.cells}


def nearest_block(cells):
    cx = sum(c[0] for c in cells) / len(cells); cz = sum(c[1] for c in cells) / len(cells)
    blocks = []
    for c in cells:
        b = {(c[0] + a, c[1] + bb) for a in (0, 1) for bb in (0, 1)}
        if b <= cells: blocks.append(b)
    if not blocks: blocks = [{c} for c in cells]
    return min(blocks, key=lambda b: sum((q[0] - cx) ** 2 + (q[1] - cz) ** 2 for q in b))


# Auto-Stuetzen: jede Deck-Unterplatte ohne Auflage bekommt eine Saeule
SEG_FLOOR = {7: 0, 11: G_DOME + 8}
_idx = top_index()
for n, plist in DECK_BOTTOM.items():
    for p in plist:
        if any((p.ybot, c) in _idx for c in p.cells): continue
        blk = nearest_block(set(p.cells))
        pillar_stack("08_innenstuetzen", blk, SEG_FLOOR[n], G_DOME + n - 1)
        _idx |= {(p.ybot, c) for c in blk}

# ---- Oberflaechen ----
def top_exposed(g):
    return {c for c in layers[g] if not covered_above(g, c)}

# T0: Studs frei (Publikum). T1: Tiles DBG ausser Saeulen-Zellen.
SCREEN = boundary8(D_T1)          # Ring Oe 56 fuer Lichtvorhang + Schirm
E_T1 = top_exposed(3)
E_LED = top_exposed(5)

# Kuppel: Cheese-Slopes an Stufenkanten
ROT_OUT = {(1, 0): 90, (-1, 0): 270, (0, 1): 180, (0, -1): 0}
for g in range(G_DOME, TOP_G):
    S = layers[g]
    for c in top_exposed(g):
        d = sector(c)
        if (c[0] + d[0], c[1] + d[1]) in S: continue
        add(Part("09_kuppel_slopes", "54200", earth_color(c), ctr(c[0]), -BH * (g + 1), ctr(c[1]), ROT_OUT[d],
                 {c}, -BH * (g + 1) - 16, -BH * (g + 1), studs=False))

# ---- Wolken / Nebel auf dem LED-Ring ----
cloud_cells = set()
ledtop_y = -BH * 6
cands = sorted(E_LED, key=lambda c: math.atan2(c[1] + 0.5, c[0] + 0.5))
for c in cands:
    if random.random() < 0.22:
        blk = {(c[0] + a, c[1] + b) for a in (0, 1) for b in (0, 1)}
        if blk <= E_LED and not (blk & cloud_cells):
            cloud_cells |= blk
            add(Part("10_nebel", "30367c", WHITE, ctr(c[0]) + 10, ledtop_y - BH, ctr(c[1]) + 10, 0, blk,
                     ledtop_y - BH, ledtop_y, studs=False))
for c in cands:
    if c in cloud_cells: continue
    if random.random() < 0.55:
        cloud_cells.add(c)
        add(Part("10_nebel", "15470", WHITE, ctr(c[0]), ledtop_y, ctr(c[1]), random.choice([0, 90, 180, 270]), {c},
                 ledtop_y - 18, ledtop_y, studs=False))
plates("10_nebel", {c: WHITE for c in E_LED - cloud_cells}, ledtop_y - PH, 0, table=TILE, studs=False)

# ---- Lichtvorhang: 24 trans-klare Rundstein-Saeulen auf dem Laufsteg ----
G_COL_TOP = 25                       # Saeulen g4..g25, Oberkante y=-624
COLS = set()
for j in range(24):
    a = 2 * math.pi * (j + 0.5) / 24
    c = (math.floor(26.7 * math.cos(a)), math.floor(26.7 * math.sin(a)))
    assert c in E_T1 and c in SCREEN, c
    COLS.add(c)
for c in COLS:
    for g in range(4, G_COL_TOP + 1):
        add(Part("12_lichtvorhang", "3062b", TCLEAR, ctr(c[0]), -BH * (g + 1), ctr(c[1]), 0, {c}, -BH * (g + 1), -BH * g))
plates("03_laufsteg", {c: DBG for c in E_T1 - COLS}, -BH * 4 - PH, 0, table=TILE, studs=False)

# ---- Schirm-Rahmen: 2 Plattenlagen kreuzweise (traegt den Schirm zwischen den Saeulen) ----
RIM = {c for r in radial_runs({c for c in ALL if 25.6 < dist(c) <= 28.6}) if set(r) & SCREEN for c in r}
y_rim = -BH * (G_COL_TOP + 1)        # -600
for p in plates("11_projektionsschirm", {c: LBG for c in RIM}, y_rim - PH, 0, tangential=True):
    p.hang = True                    # Teile ohne Saeule haengen an der Kreuzlage darueber
place_runs("11_projektionsschirm", radial_runs(RIM), LBG, y_rim - 2 * PH)

# ---- Projektionsschirm: 7 Brick-Lagen, 1 Noppe stark ----
y0 = y_rim - 2 * PH
for L in range(7):
    col = LBG if L in (0, 6) else WHITE
    pack("11_projektionsschirm", {c: col for c in SCREEN}, BRICK, y0 - BH * (L + 1), BH, L % 2)
y_scr_top = y0 - BH * 7

# ---- Truss-Ring (Gittertraeger) ----
TRUSS = SCREEN | (D_T0 - D_T1)
y = y_scr_top - PH
place_runs("13_truss_ring", radial_runs(TRUSS), DBG, y, hang=True)  # haengt teils an der Kreuzlage darueber
y -= PH
plates("13_truss_ring", {c: DBG for c in TRUSS}, y, 1)
OUTW = boundary8(D_T0)
INW = {c for c in TRUSS if any((c[0] + a, c[1] + b) not in TRUSS and dist((c[0] + a, c[1] + b)) < 27 for a, b in N8)}
for L in range(2):
    ytop = y - BH * (L + 1)
    pack("13_truss_ring", {c: BLACK for c in OUTW | INW}, TECHNIC, ytop, BH, L % 2)
y = y - 2 * BH - PH
# Obergurt: radiale Sprossen (jede 4. Reihe, inkl. Wandzellen) + Plattenring auf den Waenden
rungs = [r for r in radial_runs(TRUSS) if ((r[0][1] if sector(r[0])[0] else r[0][0]) % 4 == 0)]
place_runs("13_truss_ring", rungs, DBG, y)
rung_cells = {c for r in rungs for c in r}
plates("13_truss_ring", {c: DBG for c in (OUTW | INW) - rung_cells}, y, 0)

# Lampen unter dem Truss (haengend)
lamp_cells = set()
for j in range(24):
    a = 2 * math.pi * (j + 0.25) / 24
    c = (math.floor(29.6 * math.cos(a)), math.floor(29.6 * math.sin(a)))
    lamp_cells.add(c)
    add(Part("14_scheinwerfer", "3062b", BLACK, ctr(c[0]), y_scr_top, ctr(c[1]), 0, {c}, y_scr_top, y_scr_top + BH, hang=True))
    add(Part("14_scheinwerfer", "6141", TYELLOW, ctr(c[0]), y_scr_top + BH, ctr(c[1]), 0, {c}, y_scr_top + BH, y_scr_top + BH + PH, hang=True, studs=True))

# ---------------- Minifiguren ----------------
def mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mstr(M): return " ".join(fmt(v) for r in M for v in r)
def mv(M, v): return [sum(M[i][k] * v[k] for k in range(3)) for i in range(3)]


def minifig(sub, x, surf_y, z, rot, torso, legs, head=YELLOW, hair=None, hands=YELLOW, cells=()):
    M = RM[rot]
    P = [x, surf_y - 72, z]
    comps = [("3626bp01", head, (0, -24, 0), [[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
             ("973", torso, (0, 0, 0), [[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
             ("3818", torso, (-15.552, 9, 0), [[0.985, 0.174, 0], [-0.174, 0.985, 0], [0, 0, 1]]),
             ("3819", torso, (15.552, 9, 0), [[0.985, -0.174, 0], [0.174, 0.985, 0], [0, 0, 1]]),
             ("3820", hands, (-23.1, 24.7, -10), [[0.985, 0.174, 0], [-0.133, 0.754, -0.643], [-0.112, 0.633, 0.766]]),
             ("3820", hands, (23.1, 24.7, -10), [[0.985, -0.174, 0], [0.133, 0.754, -0.643], [0.112, 0.633, 0.766]]),
             ("3815c01", legs, (0, 32, 0), [[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
    if hair is not None: comps.append(("3901", hair, (0, -24, 0), [[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
    lines, sub_parts = [], []
    for nm, col, off, Mi in comps:
        w = mv(M, off)
        pos = [P[0] + w[0], P[1] + w[1], P[2] + w[2]]
        add(Part(sub, nm, col, pos[0], pos[1], pos[2], rot, cells if nm == "3815c01" else (), surf_y - 96 if nm == "3815c01" else 0,
                 surf_y if nm == "3815c01" else 0, studs=False,
                 extra=[f"1 {col} {fmt(pos[0])} {fmt(pos[1])} {fmt(pos[2])} {mstr(mm(M, Mi))} {nm}.dat"]))


# Performer oben auf der Kuppel (zur Front +z)
top_y = -BH * (TOP_G + 1)
minifig("15_performer", 0, top_y, 10, 180, RED, RED, hair=BLACK, cells={(-1, 0), (0, 0)})

# Publikum auf dem Basis-Rand
E_T0 = top_exposed(1)
TORSOS = [RED, BLUE, WHITE, BLACK, GREEN, YELLOW, DBG, TAN, 272]
LEGS = [BLUE, BLACK, DBG, TAN, 272]
HAIRS = [BLACK, 70, 308, TAN, BLACK]
used = set()
for j in range(28):
    a = 2 * math.pi * (j + 0.25) / 28
    px, pz = 29.6 * math.cos(a), 29.6 * math.sin(a)
    if abs(pz) >= abs(px):
        gx = round(px); k = math.floor(pz)
        cells = {(gx - 1, k), (gx, k)}
        x, z, rot = gx * LDU, ctr(k), (0 if pz > 0 else 180)
    else:
        gz = round(pz); i = math.floor(px)
        cells = {(i, gz - 1), (i, gz)}
        x, z, rot = ctr(i), gz * LDU, (270 if px > 0 else 90)
    if not cells <= E_T0 or cells & used: continue
    used |= cells
    minifig("16_publikum", x, -BH * 2, z, rot, random.choice(TORSOS), random.choice(LEGS), hair=random.choice(HAIRS), cells=cells)


# ---------------- Checks ----------------
def checks():
    idx_top = defaultdict(list)   # (ytop, cell) -> part index (Teile mit Noppen oben)
    for n, p in enumerate(parts):
        if p.studs:
            for c in p.cells: idx_top[(p.ytop, c)].append(n)
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
TITLES = {"01_baseplates": "Arena-Boden (4x Baseplate 32x32)", "02_basis": "Basis Oe64 (2 Lagen)",
          "03_laufsteg": "Laufsteg-Ring Oe56", "04_led_ring": "LED-Ring Oe52",
          "05_kuppel_unten": "Kuppel unten + Deck 1", "06_kuppel_mitte": "Kuppel Mitte + Deck 2",
          "07_kuppel_oben": "Kuppel oben", "08_innenstuetzen": "Innenstuetzen (Hohlraum)",
          "09_kuppel_slopes": "Kuppel Cheese-Slopes", "10_nebel": "Nebel / Wolken am LED-Ring",
          "11_projektionsschirm": "Projektionsschirm Oe56", "12_lichtvorhang": "Lichtvorhang (trans-clear Saeulen)",
          "13_truss_ring": "Truss-Ring Oe64", "14_scheinwerfer": "Scheinwerfer am Truss",
          "15_performer": "Performer", "16_publikum": "Publikum"}


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
    out = [f"0 FILE {NAME}.ldr", "0 Globe Stage - Konzertbuehne (LEGO MOC)", f"0 Name: {NAME}.ldr",
           "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""]
    for s in order: out += [f"0 // {TITLES.get(s, s)}", f"1 16 0 0 0 {ROT[0]} {s}.ldr"]
    out += ["0 NOFILE"]
    for s in order:
        out += [f"0 FILE {s}.ldr", f"0 {TITLES.get(s, s)}", f"0 Name: {s}.ldr"] + bysub[s] + ["0 NOFILE"]
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f"{NAME}.mpd"), "w").write("\n".join(out) + "\n")
    prev = [l for l in out if not any(f"{x}.ldr" in l and l.startswith("1 ") for x in
            ("11_projektionsschirm", "12_lichtvorhang", "13_truss_ring", "14_scheinwerfer"))]
    open(os.path.join(OUT, "preview_nocage.mpd"), "w").write("\n".join(prev) + "\n")
    bom = Counter((p.name, p.color) for p in parts)
    rows = ["LDraw Part,BrickLink ID,Name,Farbe,Menge"]; xml = ["<INVENTORY>"]
    for (nm, c), q in sorted(bom.items(), key=lambda t: (t[0][0], t[0][1])):
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
