"""
Mos Eisley Cantina - LEGO Star Wars: The Complete Saga (Hub des Spiels) - LEGO MOC Generator
Runder Raum mit 6 Episoden-Tueren, Bar mit Barkeeper, runde Tische mit weissen Stuehlen, Bacta-Tanks, Kamin,
gelbes Tor, Studs und Sammelsteine aus dem Spiel. Massstab: Minifig, 2 Baseplates 32x32.
Vorlagen: MOC-237649 (McMOC, Rebrickable) und weitere Cantina-MOCs, Spielszenen.
Pipeline: Raumform -> Waende (Verband) -> Tuer-Module (SNOT-Leuchten) -> Moebel -> Checks -> MPD/BOM/XML
Aufruf: python cantina/generate_cantina.py [ausgabeordner]
"""
import math, random, os, sys
from collections import defaultdict, Counter

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
NAME = "cantina"
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
BL_ID = {"73200b-f1": "970c00", "3070b": "3070", "3069b": "3069", "3068b": "3068", "3062b": "3062", "6141": "4073", "3815c01": "970c00", "63142": "x127c30pb01"}
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
#                          MOS EISLEY CANTINA (LEGO Star Wars: The Complete Saga)
# =====================================================================================
# Hub des Spiels: runder Raum mit den Tueren zu den Episoden, Bar mit Barkeeper in der Mitte, runde Tische
# mit weissen Stuehlen, dunkler Boden, Adobe-Waende. Vorlagen: MOC-237649 (McMOC) und weitere Cantina-MOCs.
# Koordinaten: Zellen x in [-32, 31], z in [-16, 15] (2 Baseplates 32x32 nebeneinander). VORNE = -z (offen),
# dort steht der Betrachter; Stud.io zeigt das Modell damit von vorne.
TAN, DTAN, PGOLD, TBGREEN, TLBLUE, TORANGE, TRED, LNOUGAT, SILVER = 19, 28, 297, 35, 43, 57, 36, 78, 179
COLORS.update({297: ("Pearl Gold", 115), 35: ("Trans-Bright Green", 108), 43: ("Trans-Light Blue", 15),
               57: ("Trans-Orange", 98), 36: ("Trans-Red", 17), 78: ("Light Nougat", 90), 33: ("Trans-Dark Blue", 14)})
BL_ID.update({"73200b-f1": "970c00", "4079": "4079", "6218": "6218"})
XMIN, XMAX, ZMIN, ZMAX = -32, 31, -16, 15
GRID = [(i, k) for i in range(XMIN, XMAX + 1) for k in range(ZMIN, ZMAX + 1)]
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ROT_OUT = {(1, 0): 90, (-1, 0): 270, (0, 1): 180, (0, -1): 0}      # "vorne" des Teils (Standard -z) zeigt nach d
SNOT_LINKS = []
SLING_LINKS = SNOT_LINKS          # Name, unter dem checks() seitliche Verbindungen liest
rng = random.Random(5)


def vnoise(x, z, sc=3.0, seed=0):
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx
    b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


def mat_mul(A, B):
    return [[sum(A[r][k] * B[k][c] for k in range(3)) for c in range(3)] for r in range(3)]


def mat_str(M):
    return " ".join(fmt(v) for row in M for v in row)


# ---------------- Raum: Innenflaeche mit runden hinteren Ecken, Waende 4 Noppen dick ----------------
IN_X, IN_Z, RC = 28.0, 12.0, 9.0          # Innenkante (Zellmitten), Eckradius hinten
WALL_T = 4.0                              # Wanddicke


def inside(c, grow=0.0):
    """Innenraum (grow=0) bzw. um grow Noppen vergroesserte Form (Aussenkante der Wand)"""
    x, z = c[0] + 0.5, c[1] + 0.5
    ax, az, rc = IN_X + grow, IN_Z + grow, RC + grow
    if abs(x) > ax or z > az: return False
    if z <= az - rc or abs(x) <= ax - rc: return True
    return math.hypot(abs(x) - (ax - rc), z - (az - rc)) <= rc


WALL = {c for c in GRID if not inside(c) and inside(c, WALL_T)}     # gleichmaessig dickes Band, Ecken bleiben frei
WALL_H = {c: 7 + (vnoise(c[0] + 0.5, c[1] + 0.5, 3.5, 2) > 0.5) for c in WALL}   # unruhige Oberkante (Adobe)
CUSTOM = set()                            # (Zelle, Lage) mit eigenem Aufbau (Tueren, Kamin)


def wall_color(c, g):
    v = vnoise(c[0] * 1.0 + g * 0.5, c[1] * 1.0 - g * 0.6, 3.4, 7)
    return DTAN if v > 0.72 else TAN


# ---------------- 6 Episoden-Tueren ----------------
# Tuer-Modul lokal: u entlang der Wand (-3..2), v in die Wand (0..3), Blick in den Raum (-v).
# v=0: Rahmen (u=-3, u=2) dunkelgrau, Oeffnung u=-2..1 als Nische; v=1: Rolladen (Rillensteine 2877);
# Lage 5 Sturz, Lage 6 Leuchtreihe gruen-weiss-weiss-gruen per SNOT (11211 + Rundplatten 1x1), darueber Adobe.
DOORS = [(("Episode I", (-15, 12)), (1, 0), (0, 1)), (("Episode II", (-5, 12)), (1, 0), (0, 1)),
         (("Episode III", (5, 12)), (1, 0), (0, 1)), (("Episode IV", (15, 12)), (1, 0), (0, 1)),
         (("Episode V", (-29, -1)), (0, 1), (-1, 0)), (("Episode VI", (28, -1)), (0, -1), (1, 0))]
DOOR_H, LINTEL_G, LIGHT_G = 5, 5, 6


def door_cell(o, du, dv, u, v): return (o[0] + u * du[0] + v * dv[0], o[1] + u * du[1] + v * dv[1])


R_FRONT = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]          # Noppen (lokal -y) zeigen nach -z, Koerper nach +z
DOOR_SPECS = []
for (name, o), du, dv in DOORS:
    face = (-dv[0], -dv[1])
    for u in range(-3, 3):
        for v in range(0, 2):
            c = door_cell(o, du, dv, u, v)
            assert c in WALL, (name, c)
            WALL_H[c] = 8
            for g in range(0, 7): CUSTOM.add((c, g))
    DOOR_SPECS.append((name, o, du, dv, face))

# ---------------- Kamin (linke Wand vorne) ----------------
FIRE_Z = range(-15, -9)                                # Bogen 3307 (1x6x2) entlang z, Oeffnung z -14..-11
for z in FIRE_Z:
    for g in (1, 2): CUSTOM.add(((-29, z), g))


# ---------------- Wand-Details (SNOT): Lueftungsgitter und Wandlicht zwischen den Tueren ----------------
TYELLOW_ = 46
WALL_SNOT = []                             # (Zellen, Lage, Blickrichtung, Art)
for gx in (-11, -1, 9):                    # Mitte der Luecken zwischen den Tuerrahmen der Rueckwand
    cs = [(gx, 12), (gx + 1, 12)]
    WALL_SNOT += [(cs, 2, (0, -1), "gitter"), (cs, 5, (0, -1), "licht")]
WALL_SNOT += [([(-29, -8), (-29, -7)], 3, (1, 0), "gitter"), ([(-29, -8), (-29, -7)], 5, (1, 0), "licht"),
              ([(28, -10), (28, -9)], 5, (-1, 0), "licht")]
for cs, g, face, kind in WALL_SNOT:
    for c in cs:
        assert c in WALL and WALL_H[c] > g, c
        CUSTOM.add((c, g))

# ---------------- Waende bauen ----------------
GMAX_W = 8
for g in range(GMAX_W):
    cc = {}
    for c in WALL:
        if WALL_H[c] <= g or (c, g) in CUSTOM: continue
        fire_back = c[0] == -30 and c[1] in range(-14, -10) and g in (1, 2)       # Russ hinter der Glut
        cc[c] = BLACK if fire_back else wall_color(c, g)
    bricks("02_waende", cc, g)
# Kamin: Bogen, Glut
y_arch = -BH * 3
add(Part("07_details", "3307", TAN, ctr(-29), y_arch, (ctr(-15) + ctr(-10)) / 2, 90, {(-29, -15), (-29, -10)},
         y_arch, -BH, studcells={(-29, z) for z in FIRE_Z}))
for z, col in zip(range(-14, -10), (TORANGE, TRED, TORANGE, TRED)):
    add(Part("07_details", "6141", col, ctr(-29), -BH - PH, ctr(z), 0, {(-29, z)}, -BH - PH, -BH))

# Tueren
for name, o, du, dv, face in DOOR_SPECS:
    rf = ROT_OUT[face]
    cells = lambda us, vs: {door_cell(o, du, dv, u, v): None for u in us for v in vs}
    for g in range(DOOR_H):                              # Rahmen: 1x2-Steine in die Wand hinein
        for u in (-3, 2):
            cs = [door_cell(o, du, dv, u, v) for v in (0, 1)]
            pack("03_tueren", {c: DBG for c in cs}, BRICK, -BH * (g + 1), BH, g % 2)
        for u0 in (-2, 0):                               # Rolladen: Rillensteine, Rillen zum Raum
            cs = [door_cell(o, du, dv, u0 + a, 1) for a in (0, 1)]
            cx = sum(ctr(q[0]) for q in cs) / 2; cz = sum(ctr(q[1]) for q in cs) / 2
            add(Part("03_tueren", "2877", BLACK, cx, -BH * (g + 1), cz, rf, set(cs), -BH * (g + 1), -BH * g))
    g = LINTEL_G                                         # Sturz
    pack("03_tueren", {c: DBG for c in cells(range(-3, 3), (0, 1))}, BRICK, -BH * (g + 1), BH, 0)
    g = LIGHT_G                                          # Leuchtreihe
    pack("03_tueren", {c: DBG for c in cells(range(-3, 3), (1,))}, BRICK, -BH * (g + 1), BH, 1)
    for u in (-3, 2):
        c = door_cell(o, du, dv, u, 0)
        add(Part("03_tueren", "3005", DBG, ctr(c[0]), -BH * (g + 1), ctr(c[1]), 0, {c}, -BH * (g + 1), -BH * g))
    top = -BH * (g + 1)
    M = mat_mul(RM[rf], R_FRONT)
    for u0 in (-2, 0):
        cs = [door_cell(o, du, dv, u0 + a, 0) for a in (0, 1)]
        cx = sum(ctr(q[0]) for q in cs) / 2; cz = sum(ctr(q[1]) for q in cs) / 2
        holder = add(Part("03_tueren", "11211", DBG, cx, top, cz, rf, set(cs), top, top + BH))
        for q, col in zip(cs, (TBGREEN, WHITE) if u0 == -2 else (WHITE, TBGREEN)):
            fc = (q[0] + face[0], q[1] + face[1])        # Licht ragt in die Zelle davor
            lx, ly, lz = ctr(q[0]) + face[0] * 18, top + 10, ctr(q[1]) + face[1] * 18
            lamp = add(Part("03_tueren", "6141", col, lx, ly, lz, rf, {fc}, ly - 10, ly + 10, studs=False, hang=True,
                            extra=[f"1 {col} {fmt(lx)} {fmt(ly)} {fmt(lz)} {mat_str(M)} 6141.dat"]))
            SNOT_LINKS.append((lamp, holder))
    ths = [door_cell(o, du, dv, u, 0) for u in range(-2, 2)]
    cx = sum(ctr(q[0]) for q in ths) / 4; cz = sum(ctr(q[1]) for q in ths) / 4
    add(Part("03_tueren", "2431", LBG, cx, -PH, cz, 0 if du[0] else 90, set(ths), -PH, 0, studs=False))

for cs, g, face, kind in WALL_SNOT:
    rf = ROT_OUT[face]; top = -BH * (g + 1); M = mat_mul(RM[rf], R_FRONT)
    cx = sum(ctr(q[0]) for q in cs) / 2; cz = sum(ctr(q[1]) for q in cs) / 2
    holder = add(Part("02_waende", "11211", TAN, cx, top, cz, rf, set(cs), top, top + BH))
    fcs = {(q[0] + face[0], q[1] + face[1]) for q in cs}
    if kind == "gitter":
        gx_, gy_, gz_ = cx + face[0] * 18, top + 10, cz + face[1] * 18
        vent = add(Part("02_waende", "2412b", DBG, gx_, gy_, gz_, rf, fcs, gy_ - 10, gy_ + 10, studs=False, hang=True,
                        extra=[f"1 {DBG} {fmt(gx_)} {fmt(gy_)} {fmt(gz_)} {mat_str(M)} 2412b.dat"]))
        SNOT_LINKS.append((vent, holder))
    else:
        for q in cs:
            lx, ly, lz = ctr(q[0]) + face[0] * 18, top + 10, ctr(q[1]) + face[1] * 18
            lamp = add(Part("02_waende", "6141", TYELLOW_, lx, ly, lz, rf, {(q[0] + face[0], q[1] + face[1])}, ly - 10, ly + 10,
                            studs=False, hang=True, extra=[f"1 {TYELLOW_} {fmt(lx)} {fmt(ly)} {fmt(lz)} {mat_str(M)} 6141.dat"]))
            SNOT_LINKS.append((lamp, holder))

# Wandkrone: offene Oberseiten mit gebogenen Slopes (weiche Adobe-Kante zum Raum) und Fliesen
TREASURE = []                                            # (Teil, Farbe, Zellen) - Sammelsteine aus dem Spiel
def top_h(c): return WALL_H.get(c, 0)
spots = [(("3004", PGOLD), ((-10, 13), (-9, 13))), (("3004", PGOLD), ((9, 13), (10, 13))),
         (("3004", 4), ((-30, -8), (-30, -7))), (("3004", PGOLD), ((29, -8), (29, -7))), (("3004", 4), ((-25, 11), (-24, 11))),
         (("3062b", 47), ((0, 14),)), (("3062b", 47), ((-31, 0),)), (("3062b", 47), ((30, -13),)), (("3062b", 47), ((24, 12),))]
for (nm, col), cs in spots:
    if all(c in WALL for c in cs) and len({top_h(c) for c in cs}) == 1: TREASURE.append((nm, col, cs))
TREASURE_CELLS = {c for _, _, cs in TREASURE for c in cs}
caps = defaultdict(dict); done = set()
for c in sorted(WALL):
    if c in TREASURE_CELLS or c in done: continue
    h = top_h(c); y = -BH * h
    drop = [d for d in DIRS if top_h((c[0] + d[0], c[1] + d[1])) < h]
    room = [d for d in drop if inside((c[0] + d[0], c[1] + d[1]))]
    col = wall_color(c, h - 1)
    if room and vnoise(c[0] + 0.5, c[1] + 0.5, 1.9, 5) < 0.55:
        d = room[0]; i = (c[0] - d[0], c[1] - d[1])
        if i in WALL and top_h(i) == h and i not in done and i not in TREASURE_CELLS and i not in caps[h]:
            add(Part("02_waende", "11477", col, (ctr(c[0]) + ctr(i[0])) / 2, y, (ctr(c[1]) + ctr(i[1])) / 2, ROT_OUT[d],
                     {c, i}, y - 16, y, studs=False))
            done |= {c, i}; continue
    if drop and vnoise(c[0] + 0.5, c[1] + 0.5, 1.4, 9) < 0.5:
        add(Part("02_waende", "54200", col, ctr(c[0]), y, ctr(c[1]), ROT_OUT[drop[0]], {c}, y - 16, y, studs=False))
        done.add(c); continue
    caps[h][c] = col
for h, cc in caps.items():
    plates("02_waende", cc, -BH * h - PH, h % 2, table=TILE, studs=False)
for nm, col, cs in TREASURE:
    y = -BH * top_h(cs[0])
    cx = sum(ctr(q[0]) for q in cs) / len(cs); cz = sum(ctr(q[1]) for q in cs) / len(cs)
    add(Part("07_details", nm, col, cx, y - BH, cz, 0 if len({q[1] for q in cs}) == 1 else 90, set(cs), y - BH, y))
    if nm == "3062b":                                     # Minikit: rotes Teil im Behaelter
        add(Part("07_details", "6141", 4, cx, y - BH - PH, cz, 0, set(cs), y - BH - PH, y - BH))

# ---------------- Bar in der Mitte ----------------
BX0, BX1, BZ0, BZ1 = -11, 8, -5, 0                      # Aussenmass der Theke
BAR = {(x, z) for x in range(BX0, BX1 + 1) for z in range(BZ0, BZ1 + 1)
       if x <= BX0 + 1 or x >= BX1 - 1 or z <= BZ0 + 1 or z >= BZ1 - 1}
BAR -= {(x, z) for x in (-1, 0) for z in (BZ1 - 1, BZ1)}   # Durchgang hinten fuer den Barkeeper
CORNERS = {(BX0, BZ0): 270, (BX1 - 1, BZ0): 0, (BX1 - 1, BZ1 - 1): 90, (BX0, BZ1 - 1): 180}   # Rundung nach aussen


def place_2x2(sub, name, col, cmin, r, ytop, ybot, studs=True):
    """2x2-Teil mit Ursprung in einer Eckzelle (lokal (0,0),(1,0),(0,-1),(1,-1)) auf den Block ab cmin setzen"""
    R = RM[r]
    offs = [(round(R[0][0] * a + R[0][2] * b), round(R[2][0] * a + R[2][2] * b)) for a, b in ((0, 0), (1, 0), (0, -1), (1, -1))]
    o = (cmin[0] - min(q[0] for q in offs), cmin[1] - min(q[1] for q in offs))
    cs = {(o[0] + q[0], o[1] + q[1]) for q in offs}
    return add(Part(sub, name, col, ctr(o[0]), ytop, ctr(o[1]), r, cs, ytop, ybot, studs))
CORNER_CELLS = {(x + a, z + b) for (x, z) in CORNERS for a in (0, 1) for b in (0, 1)}
for g in range(2):
    bricks("04_bar", {c: WHITE for c in BAR - CORNER_CELLS}, g)
    for (x, z), r in CORNERS.items():
        place_2x2("04_bar", "3063b", WHITE, (x, z), r, -BH * (g + 1), -BH * g)
yt = -2 * BH - PH
CUP_CELLS = [(-8, BZ0), (-3, BZ0), (3, BZ0)]
plates("04_bar", {c: WHITE for c in BAR - CORNER_CELLS - set(CUP_CELLS)}, yt, 1, table=TILE, studs=False)
for c, col in zip(CUP_CELLS, (47, WHITE, 47)):          # Untersetzer (Platte 1x1) mit Becher
    add(Part("04_bar", "3024", WHITE, ctr(c[0]), yt, ctr(c[1]), 0, {c}, yt, yt + PH))
    add(Part("04_bar", "3899", col, ctr(c[0]), yt - 24, ctr(c[1]), 0, {c}, yt - 24, yt, studs=False))
for (x, z), r in CORNERS.items():
    place_2x2("04_bar", "27925", WHITE, (x, z), r, yt, yt + PH, studs=False)
# Rueckbar (dunkelgrau, 3 Steine) mit Flaschen und Faessern, Luecke fuer den Barkeeper
BACK = [(x, BZ0 + 3) for x in range(BX0 + 2, BX1 - 1) if x not in (-1, 0)]
for g in range(3):
    bricks("04_bar", {c: DBG for c in BACK}, g)
ITEMS = [("3062b", 70), ("6141", TLBLUE), ("3062b", 70), ("6141", 47), ("6141", TRED), ("3062b", DTAN),
         ("6141", TBGREEN), ("3062b", 70), ("6141", 47), ("6141", TLBLUE), ("3062b", DTAN), ("6141", TRED)]
for c in BACK[len(ITEMS):]:                              # Zapfhaehne
    add(Part("04_bar", "4589", LBG, ctr(c[0]), -BH * 4, ctr(c[1]), 0, {c}, -BH * 4, -BH * 3))
for c, (nm, col) in zip(BACK, ITEMS):
    y0 = -BH * 3
    if nm == "3062b": add(Part("04_bar", nm, col, ctr(c[0]), y0 - BH, ctr(c[1]), 0, {c}, y0 - BH, y0))
    else:
        add(Part("04_bar", nm, col, ctr(c[0]), y0 - PH, ctr(c[1]), 0, {c}, y0 - PH, y0))
        add(Part("04_bar", nm, col, ctr(c[0]), y0 - 2 * PH, ctr(c[1]), 0, {c}, y0 - 2 * PH, y0 - PH))
# Hocker vor der Theke
for x in range(BX0 + 2, BX1 - 1, 3):
    c = (x, BZ0 - 1)
    add(Part("04_bar", "3062b", BLACK, ctr(x), -BH, ctr(c[1]), 0, {c}, -BH, 0))
    add(Part("04_bar", "6141", 4, ctr(x), -BH - PH, ctr(c[1]), 0, {c}, -BH - PH, -BH))

RING = {(x, z) for x in range(BX0 - 1, BX1 + 2) for z in range(BZ0 - 1, BZ1 + 2)
        if (x in (BX0 - 1, BX1 + 1) or z == BZ1 + 1)}      # Fliesenkante links, rechts, hinten (vorne die Hocker)
plates("04_bar", {c: LBG for c in RING}, -PH, 0, table=TILE, studs=False)

# ---------------- Runde Tische mit weissen Stuehlen ----------------
TABLES = [(-18, -9), (-19, 5), (0, 7), (16, 6), (13, -10)]      # Mittelpunkt auf dem Raster (Zellgrenze)
for (tx, tz) in TABLES:
    post = {(tx + a, tz + b) for a in (-1, 0) for b in (-1, 0)}
    add(Part("05_tische", "3941", LBG, tx * LDU, -BH, tz * LDU, 0, post, -BH, 0))
    top = {(tx + a, tz + b) for a in range(-2, 2) for b in range(-2, 2)}
    add(Part("05_tische", "60474", WHITE, tx * LDU, -BH - PH, tz * LDU, 0, top, -BH - PH, -BH))
    mid = {(tx + a, tz + b) for a in (-1, 0) for b in (-1, 0)}
    add(Part("05_tische", "6141", 46, tx * LDU, -BH - 2 * PH, tz * LDU, 0, mid, -BH - 2 * PH, -BH - PH))   # Kerze
    cup = (tx - 2, tz - 1)
    add(Part("05_tische", "3899", 4, ctr(cup[0]), -BH - PH - 24, ctr(cup[1]), 90, {cup}, -BH - PH - 24, -BH - PH, studs=False))
    for (dx, dz), f in (((-4, -1), (1, 0)), ((2, -1), (-1, 0)), ((-1, -4), (0, 1))):
        cs = {(tx + dx + a, tz + dz + b) for a in (0, 1) for b in (0, 1)}
        cx = sum(ctr(q[0]) for q in cs) / 4; cz = sum(ctr(q[1]) for q in cs) / 4
        add(Part("05_tische", "4079", WHITE, cx, -PH, cz, ROT_OUT[f], cs, -PH - 40, 0, studs=False))

# ---------------- Bacta-Tanks (rechts vorne) ----------------
TANKS = [(25, -12), (25, -6)]
for (tx, tz) in TANKS:
    cs = {(tx + a, tz + b) for a in range(-2, 2) for b in range(-2, 2)}
    add(Part("06_bacta", "87081", DBG, tx * LDU, -BH, tz * LDU, 0, cs, -BH, 0))
    yb = -BH - 96
    for r, half in ((0, {(tx + a, tz + b) for a in range(-2, 2) for b in (-2, -1)}),
                    (180, {(tx + a, tz + b) for a in range(-2, 2) for b in (0, 1)})):
        add(Part("06_bacta", "6218", TLBLUE, tx * LDU, yb, tz * LDU, r, half, yb, -BH))
    add(Part("06_bacta", "87081", LBG, tx * LDU, yb - BH, tz * LDU, 0, cs, yb - BH, yb))
    add(Part("06_bacta", "60474", DBG, tx * LDU, yb - BH - PH, tz * LDU, 0, cs, yb - BH - PH, yb - BH))

# ---------------- Gelbes Tor (links vorne) ----------------
GX, GZ = -26, (-9, -6)
for z in GZ:
    for g in range(4):
        add(Part("07_details", "3005", 14, ctr(GX), -BH * (g + 1), ctr(z), 0, {(GX, z)}, -BH * (g + 1), -BH * g))
ya = -BH * 6
add(Part("07_details", "6182", 14, ctr(GX), ya, (ctr(GZ[0]) + ctr(GZ[1])) / 2, 90, {(GX, z) for z in range(GZ[0], GZ[1] + 1)}, ya, -BH * 4))

# ---------------- Figuren (optional, eigene Baugruppe) ----------------
FIGURES = {
    "barkeeper": [("73200b-f1", 308, -40), ("76382", DTAN, -72), ("3626c", LNOUGAT, -96), ("3901", 308, -96)],
    "schmuggler": [("73200b-f1", BLACK, -40), ("76382", WHITE, -72), ("3626c", LNOUGAT, -96), ("3901", 70, -96)],
    "trooper": [("73200b-f1", WHITE, -40), ("76382", WHITE, -72), ("3626c", BLACK, -96), ("30408", WHITE, -96)],
}
FIG_STANDS = [("barkeeper", (-1, BZ0 + 3), (0, BZ0 + 3), (0, -1)),        # in der Luecke der Rueckbar
              ("schmuggler", (-13, -12), (-12, -12), (0, -1)),
              ("trooper", (21, -9), (21, -8), (-1, 0))]
for kind, a, b, out in FIG_STANDS:
    rot = ROT_OUT[out]; R = RM[rot]
    X, Z = (ctr(a[0]) + ctr(b[0])) / 2, (ctr(a[1]) + ctr(b[1])) / 2
    for name, col, oy in FIGURES[kind]:
        wx, wy, wz = X + R[0][1] * oy, R[1][1] * oy, Z + R[2][1] * oy
        if name.startswith("73200"):
            add(Part("08_figuren", name, col, wx, wy, wz, rot, {a, b}, -112, 0, studs=False))
        else:
            add(Part("08_figuren", name, col, wx, wy, wz, rot, set(), wy, wy, studs=False))

# ---------------- Einrichtung: Trittplatten, Faesser, Kisten, R2, Kontrollpult ----------------
for name, o, du, dv, face in DOOR_SPECS:                 # Trittplatte vor jeder Tuer
    pad = [(door_cell(o, du, dv, u, 0)[0] + face[0], door_cell(o, du, dv, u, 0)[1] + face[1]) for u in range(-2, 2)]
    cx = sum(ctr(q[0]) for q in pad) / 4; cz = sum(ctr(q[1]) for q in pad) / 4
    add(Part("07_details", "2431", LBG, cx, -PH, cz, 0 if du[0] else 90, set(pad), -PH, 0, studs=False))


def block(sub, name, col, x0, z0, ytop, h, studs=True, rot=0, studcells=None):
    cs = {(x0 + a, z0 + b) for a in (0, 1) for b in (0, 1)}
    return add(Part(sub, name, col, (x0 + 1) * LDU, ytop, (z0 + 1) * LDU, rot, cs, ytop, ytop + h, studs, studcells=studcells))


for (x0, z0) in ((-22, 8), (19, 9), (-24, -15)):         # Faesser (2 uebereinander)
    block("07_details", "3941", 70, x0, z0, -BH, BH); block("07_details", "3941", 70, x0, z0, -2 * BH, BH)
for (x0, z0, n) in ((-20, 9, 1), (-27, -15, 2)):          # Kisten mit Deckel
    for k in range(n): block("07_details", "3003", DTAN, x0, z0, -BH * (k + 1), BH)
    block("07_details", "3068b", DTAN, x0, z0, -BH * n - PH, PH, studs=False)
block("07_details", "4032a", DBG, 10, -3, -PH, PH)          # R2-Einheit
block("07_details", "3941", WHITE, 10, -3, -PH - BH, BH)
block("07_details", "30367c", SILVER, 10, -3, -PH - 2 * BH, BH)
block("06_bacta", "3003", DBG, 24, -10, -BH, BH)          # Kontrollpult zwischen den Tanks, Schraege zum Raum
pult = block("06_bacta", "3039", DBG, 24, -10, -2 * BH, BH, rot=270, studcells={(25, -10), (25, -9)})
pult.x += 10                                              # Ursprung der Schraege liegt 10 LDU hinter der Mitte
for z, col in ((-10, TBGREEN), (-9, TRED)):
    add(Part("06_bacta", "6141", col, ctr(25), -2 * BH - PH, ctr(z), 0, {(25, z)}, -2 * BH - PH, -2 * BH))
for (x, z), col in (((-1, -15), SILVER), ((0, -13), SILVER), ((-1, -11), PGOLD), ((0, -9), SILVER)):   # Stud-Spur zur Bar
    add(Part("07_details", "98138", col, ctr(x), -PH, ctr(z), 0, {(x, z)}, -PH, 0, studs=False))
for (x0, z0) in ((5, -14), (-8, 9)):                      # grosse blaue Studs
    block("07_details", "14769", 1, x0, z0, -PH, PH, studs=False)

# ---------------- Studs (Spielwaehrung) auf dem Boden ----------------
occupied0 = {c for p in parts for c in p.cells if p.ybot >= -1 and p.name not in ("3811",)}
free = [c for c in GRID if inside(c) and c not in occupied0
        and all((c[0] + a, c[1] + b) not in occupied0 for a, b in N8)]
rng.shuffle(free)
studs_ = []
for c in free:
    if len(studs_) >= 26: break
    if any(abs(c[0] - q[0]) + abs(c[1] - q[1]) < 4 for q in studs_): continue
    studs_.append(c)
STUD_COLS = [SILVER, SILVER, SILVER, PGOLD, PGOLD, 1]
for i, c in enumerate(studs_):
    add(Part("07_details", "98138", STUD_COLS[i % len(STUD_COLS)], ctr(c[0]), -PH, ctr(c[1]), 0, {c}, -PH, 0, studs=False))

# ---------------- Grundplatten ----------------
for sx in (-1, 1):
    cells = {(i, k) for i in (range(0, 32) if sx > 0 else range(-32, 0)) for k in range(-16, 16)}
    add(Part("01_grundplatten", "3811", DBG, sx * 320, 0, 0, 0, cells, 0, 4, True))

TITLES = {"01_grundplatten": "Grundplatten (2x 32x32, dunkelgrau)", "02_waende": "Adobe-Waende mit runden Ecken",
          "03_tueren": "6 Episoden-Tueren", "04_bar": "Bar mit Rueckbar und Hockern", "05_tische": "Runde Tische mit Stuehlen",
          "06_bacta": "Bacta-Tanks", "07_details": "Kamin, Tor, Sammelsteine, Studs", "08_figuren": "Figuren (optional)"}


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
    out = [f"0 FILE {NAME}.ldr", "0 Mos Eisley Cantina - LEGO Star Wars: The Complete Saga (LEGO MOC)", f"0 Name: {NAME}.ldr",
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

