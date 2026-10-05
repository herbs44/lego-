"""
Saint Pablo Tour (Kanye West, 2016) - schwebende Buehne - LEGO MOC Generator
Plattform mit Gittertraegern und PAR-Lampen, an 4 Seilen unter einem riesigen Lichtraster mit hunderten haengenden
Leuchten (Trans-Orange), auf 6 Gittertuermen; darunter das Publikum als Moshpit. Massstab: Minifig, Baseplate 48x48.
Vorlagen: Konzertfotos und Berichte zur Tour (Plattform ca. 16 x 20 ft, ca. 15 ft ueber dem Publikum, an Motoren
unter dem Licht-Rig). Pipeline: Hoehen aus der Seillaenge -> Plattform -> Tuerme/Raster -> Seile -> Leuchten ->
Figuren -> Checks -> MPD/BOM/XML
Aufruf: python saint-pablo/generate_saint_pablo.py [ausgabeordner]
"""
import math, random, os, sys
from collections import defaultdict, Counter

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
NAME = "saint_pablo"
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
#                           SAINT PABLO TOUR (Kanye West, 2016)
# =====================================================================================
# Schwebende Buehne: Plattform (16 x 20 ft, hier 16 x 12 Noppen) mit Gittertraegern und PAR-Lampen, an 4 Seilen
# unter einem riesigen Lichtraster mit hunderten haengenden Leuchten, darunter das Publikum als Moshpit.
# Koordinaten: Zellen x, z in [-24, 23] (Baseplate 48x48). VORNE = -z.
TORANGE, TYELLOW_, TRED, TCLEAR_, DTAN, RBROWN, LNOUGAT, MNOUGAT, NOUGAT, DBROWN, DBLUE = 57, 46, 36, 47, 28, 70, 78, 84, 92, 308, 272
COLORS.update({57: ("Trans-Orange", 98), 36: ("Trans-Red", 17), 78: ("Light Nougat", 90), 84: ("Medium Nougat", 150),
               92: ("Nougat", 28), 308: ("Dark Brown", 120), 272: ("Dark Blue", 63)})
BL_ID.update({"73200b-f1": "970c00"})
XMIN, XMAX, ZMIN, ZMAX = -24, 23, -24, 23
GROUND = "4186"
SLING_LINKS = []                            # seitliche/haengende Verbindungen (Seile, Traeger-Stege), vom Check gelesen


def vnoise(x, z, sc=3.0, seed=0):
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx
    b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


def girder(sub, x0, x1, zc, ytop):
    """Gittertraeger 30518 (2 x 16) ueber die Zellen x0..x1, Zeilen zc-1 und zc. Die Noppen oben stecken in der Lage
    darueber. Endbloecke 2 x 2 (24 LDU hoch) mit Noppenaufnahmen unten, dazwischen der Steg bis 45 LDU (eigenes Volumen)."""
    assert x1 - x0 == 15
    cells = {(x, z) for x in range(x0, x1 + 1) for z in (zc - 1, zc)}
    g = add(Part(sub, "30518", BLACK, (x0 + 8) * LDU, ytop, zc * LDU, 0, cells, ytop, ytop + BH, hang=True))
    web = {(x, z) for x in range(x0 + 2, x1 - 1) for z in (zc - 1, zc)}
    steg = add(Part(sub, "_steg", BLACK, 0, 0, 0, 0, web, ytop + BH, ytop + 45, studs=False, hang=True,
                    extra=["0 // Steg des Gittertraegers (nur Kollisionsvolumen)"]))
    SLING_LINKS.append((steg, g))
    return g


# ---------------- Hoehen (aus der festen Seillaenge 63142: 576 LDU Schnur zwischen den Endnoppen) ----------------
ROPE_FREE, KNOB, ROPE_R, BEND, JOG = 576, 8, 2, 12, 14
N_BASE = 4                                   # Turmsockel in Steinen, darauf 3 Gittertuerme 95347 (je 10 Steine)
RB = -(N_BASE * BH + 3 * 240)                # Unterkante des Lichtrasters = Oberkante der Tuerme
H_ROPE = ROPE_FREE - 2 * BEND - 2 * JOG      # Abstand der beiden Endnoppen (Spitze zu Spitze)
YG = RB + H_ROPE                             # Oberkante der Plattform-Traeger (= Unterkante der unteren Deckplatten)
Y1 = YG - PH                                 # untere Deckplatten
Y_SURF = Y1 - PH                             # Oberkante der oberen Deckplatten (Kanye steht hier, zwischen den Fliesen)
Y_DECK = Y_SURF - PH                         # Oberkante der Fliesen

# ---------------- Plattform ----------------
PX0, PX1, PZ0, PZ1 = -8, 7, -6, 5            # 16 x 12 Noppen
DECK = {(x, z) for x in range(PX0, PX1 + 1) for z in range(PZ0, PZ1 + 1)}
p1 = plates("06_plattform", {c: BLACK for c in DECK}, Y1, 0)
p2, ncomp = bond_layer("06_plattform", DECK, p1, Y_SURF, BLACK)
assert ncomp == 1, ncomp
KANYE = [(-1, -3), (0, -3)]                  # Standplatz vorne mittig (Fuesse auf den Noppen, Fliesen drumherum)
# Randleuchten: jede zweite Randzelle eine Rundplatte Trans-Clear zwischen den Fliesen (leuchtender Umriss)
RIM = sorted(c for c in DECK if (c[0] in (PX0, PX1) or c[1] in (PZ0, PZ1)) and (c[0] + c[1]) % 2 == 0)
for c in RIM:
    add(Part("06_plattform", "6141", TCLEAR_, ctr(c[0]), Y_DECK, ctr(c[1]), 0, {c}, Y_DECK, Y_SURF))
plates("06_plattform", {c: BLACK for c in DECK - set(KANYE) - set(RIM)}, Y_DECK, 1, table=TILE, studs=False)
# Rand: Gittertraeger 2x16 an den Laengsseiten, Zaeune 1x4x2 an den Stirnseiten - haengen mit den Noppen im Deck
PGIRDERS = [girder("06_plattform", PX0, PX1, zc, YG) for zc in (PZ0 + 1, PZ1)]
for x in (PX0, PX1):
    for z0 in (PZ0 + 2, PZ0 + 6):
        cells = {(x, z) for z in range(z0, z0 + 4)}
        add(Part("06_plattform", "15332", BLACK, ctr(x), YG, (z0 + 2) * LDU, 90, cells, YG, YG + 48, hang=True))
# PAR-Lampen innen am Rand, Downlights in der Mitte (Rundstein 1x1 + Rundplatte, haengen unter dem Deck)
PAR = [(x, PZ0 + 2) for x in range(PX0 + 1, PX1, 2)] + [(x, PZ1 - 2) for x in range(PX0 + 1, PX1, 2)] + \
      [(PX0 + 1, z) for z in (PZ0 + 4, PZ0 + 6)] + [(PX1 - 1, z) for z in (PZ0 + 4, PZ0 + 6)]
DOWN = [(x, z) for x in range(PX0 + 3, PX1 - 1, 3) for z in (-1, 0)]
for c in PAR + DOWN:
    col = TYELLOW_ if c in PAR else TCLEAR_
    add(Part("06_plattform", "3062b", BLACK, ctr(c[0]), YG, ctr(c[1]), 0, {c}, YG, YG + BH, hang=True))
    add(Part("06_plattform", "6141", col, ctr(c[0]), YG + BH, ctr(c[1]), 0, {c}, YG + BH, YG + BH + PH, hang=True))

# ---------------- Tuerme und Lichtraster ----------------
TOWERS = [(-24, -24), (22, -24), (-24, -1), (22, -1), (-24, 22), (22, 22)]      # untere linke Zelle des 2x2
TOWER_CELLS = {(x + a, z + b) for x, z in TOWERS for a in (0, 1) for b in (0, 1)}
for x, z in TOWERS:
    base = {(x + a, z + b): BLACK for a in (0, 1) for b in (0, 1)}
    for g in range(N_BASE):
        pack("02_tuerme", base, BRICK, -BH * (g + 1), BH, g % 2)
    yy = -BH * N_BASE
    for k in range(3):
        yy -= 240
        add(Part("02_tuerme", "95347", BLACK, (x + 1) * LDU, yy, (z + 1) * LDU, 0, set(base), yy, yy + 240))
assert yy == RB, (yy, RB)
XBEAM_Z = [(-24, -23), (-18, -17), (-12, -11), (PZ0, PZ0 + 1), (-1, 0), (PZ1 - 1, PZ1), (10, 11), (16, 17), (22, 23)]
ZBEAM_X = [(-24, -23), (-17, -16), (-9, -8), (-1, 0), (7, 8), (15, 16), (22, 23)]
LATTICE = {(x, z) for pair in XBEAM_Z for z in pair for x in range(XMIN, XMAX + 1)} | \
          {(x, z) for pair in ZBEAM_X for x in pair for z in range(ZMIN, ZMAX + 1)}
r1 = plates("03_rig", {c: BLACK for c in LATTICE}, RB - PH, 0)
for p in r1:
    if not (p.cells & TOWER_CELLS): p.hang = True
r2, ncomp = bond_layer("03_rig", LATTICE, r1, RB - 2 * PH, BLACK)
assert ncomp == 1, ncomp
for p in r2: p.hang = True
# Steinlage im Verband obenauf: macht jeden Rasterbalken 40 LDU hoch (2 Platten + 1 Stein) - steif genug fuer die
# Spannweite von 46 Noppen zwischen den Tuermen und die Last aus Leuchten und Plattform
r3 = pack("03_rig", {c: BLACK for c in LATTICE}, BRICK, RB - 2 * PH - BH, BH, 1)
RIG_TOP = RB - 2 * PH - BH
# Haupttraeger ueber der Plattform: je 3 Gittertraeger 30518 unter den Rasterreihen der Plattform-Laengsseiten
RGIRDERS = {}
for zc in (PZ0 + 1, PZ1):
    for x0 in (-24, -8, 8):
        RGIRDERS[(x0, zc)] = girder("03_rig", x0, x0 + 15, zc, RB)


# ---------------- Seile 63142: oben im Endblock des Rig-Traegers, unten von unten im Endblock des Plattform-Traegers ----
def rope_file():
    h = H_ROPE
    L = ["0 Seil 63142 (String with End Studs 30L): oberer Knopf im Rig-Traeger, unterer Knopf von unten im Plattform-Traeger",
         "0 // Schnur laeuft aussen an der Plattform vorbei und im J-Bogen von unten in den unteren Knopf"]
    for y0 in (0, h):                              # Knoepfe: Noppe nach oben, Koerper darunter
        L += [f"1 16 0 {fmt(y0)} 0 1 0 0 0 1 0 0 0 1 stud.dat",
              f"1 16 0 {fmt(y0)} 0 6 0 0 0 1 0 0 0 6 4-4disc.dat",
              f"1 16 0 {fmt(y0)} 0 6 0 0 0 {KNOB} 0 0 0 6 4-4cyli.dat",
              f"1 16 0 {fmt(y0 + KNOB)} 0 6 0 0 0 1 0 0 0 6 4-4disc.dat"]
    R = ROPE_R
    def vert(x, y1, y2): return f"1 16 {fmt(x)} {fmt(y1)} 0 {R} 0 0 0 {fmt(y2 - y1)} 0 0 0 {R} 4-4cyli.dat"
    def horz(x1, x2, y): return f"1 16 {fmt(x1)} {fmt(y)} 0 0 {fmt(x2 - x1)} 0 {R} 0 0 0 0 {R} 4-4cyli.dat"
    def knee(x, y): return f"1 16 {fmt(x)} {fmt(y)} 0 {R} 0 0 0 {R} 0 0 0 {R} 8-8sphe.dat"
    y_top, y_bot = KNOB + BEND, h + KNOB + BEND
    L += [vert(0, KNOB, y_top), horz(0, JOG, y_top), vert(JOG, y_top, y_bot), horz(0, JOG, y_bot), vert(0, h + KNOB, y_bot),
          knee(0, y_top), knee(JOG, y_top), knee(JOG, y_bot), knee(0, y_bot)]
    assert BEND + JOG + (y_bot - y_top) + JOG + BEND == ROPE_FREE
    return L


CUSTOM_FILES = {"seil_63142.ldr": rope_file()}
ROPE_CELLS = [(PX0, PZ0), (PX1, PZ0), (PX0, PZ1), (PX1, PZ1)]          # Ecken der Plattform = Endbloecke beider Traeger
for c in ROPE_CELLS:
    zc = PZ0 + 1 if c[1] < 0 else PZ1
    rot = 270 if c[1] < 0 else 90                                         # Schnur (lokal +x) nach aussen
    y = RB + BH
    line = f"1 0 {fmt(ctr(c[0]))} {fmt(y)} {fmt(ctr(c[1]))} {ROT[rot]} seil_63142.ldr"
    rope = add(Part("05_seile", "63142", BLACK, ctr(c[0]), y, ctr(c[1]), rot, {c}, y, y + KNOB, hang=True, extra=[line]))
    SLING_LINKS.append((rope, PGIRDERS[0 if c[1] < 0 else 1]))           # Plattform haengt am unteren Knopf
    assert c in RGIRDERS[(-8, zc)].cells

# ---------------- Lichtraster: haengende Leuchten ----------------
BLOCKED = TOWER_CELLS | {c for g in RGIRDERS.values() for c in g.cells}
NEAR_ROPE = {(c[0] + a, c[1] + b) for c in ROPE_CELLS for a in (-1, 0, 1) for b in (-2, -1, 0, 1, 2)}
LAMP_CELLS = set()
for za, zb in XBEAM_Z:                                   # entlang der Querreihen versetzt (Zickzack)
    for x in range(XMIN, XMAX + 1):
        LAMP_CELLS.add((x, za) if x % 2 == 0 else (x, zb))
for xa, xb in ZBEAM_X:                                   # entlang der Laengsreihen
    for z in range(ZMIN, ZMAX + 1):
        LAMP_CELLS.add((xa, z) if z % 2 == 0 else (xb, z))
LAMP_CELLS = sorted(c for c in LAMP_CELLS if c not in BLOCKED and c not in NEAR_ROPE)
LAMPS = 0
for c in LAMP_CELLS:
    x, z = c
    d = math.hypot(x + 0.5, z + 0.5)
    n = 1 + int(1.3 * max(0.0, 1 - d / 30) + vnoise(x, z, 3, 4) * 0.9)
    col = TORANGE if vnoise(x, z, 4, 8) < 0.8 else TYELLOW_
    y = RB
    for k in range(n):
        add(Part("04_lichtraster", "3062b", BLACK, ctr(x), y, ctr(z), 0, {c}, y, y + BH, hang=True)); y += BH
    add(Part("04_lichtraster", "6141", col, ctr(x), y, ctr(z), 0, {c}, y, y + PH, hang=True))
    LAMPS += 1
print("Leuchten im Raster:", LAMPS)


# ---------------- Minifiguren ----------------
def mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mstr(M): return " ".join(fmt(round(v, 4)) for r in M for v in r)
def mv(M, v): return [sum(M[i][k] * v[k] for k in range(3)) for i in range(3)]
def rx(deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[1, 0, 0], [0, c, -s_], [0, s_, c]]
I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def minifig(sub, cells, surf_y, rot, torso, legs, head, hair=None, arms=(0, 0), mic=False):
    """Minifigur auf den Noppen 'cells' (2 Zellen), Blick lokal nach -z; arms = Hebewinkel rechts/links (negativ = nach
    vorne/oben). Rechter Arm (3818) liegt bei -x. mic=True: Mikrofon 90370 in der rechten Hand."""
    M = RM[rot]
    cx = sum(ctr(c[0]) for c in cells) / 2; cz = sum(ctr(c[1]) for c in cells) / 2
    P = [cx, surf_y - 72, cz]
    comps = [("3626c", head, (0, -24, 0), I3), ("973", torso, (0, 0, 0), I3), ("73200b-f1", legs, (0, 32, 0), I3)]
    for sgn, arm, a in ((-1, "3818", arms[0]), (1, "3819", arms[1])):
        A0 = [[0.985, -sgn * 0.174, 0], [sgn * 0.174, 0.985, 0], [0, 0, 1]]
        H0 = [[0.985, -sgn * 0.174, 0], [-sgn * -0.133, 0.754, -0.643], [-sgn * -0.112, 0.633, 0.766]]
        piv = (sgn * 15.552, 9, 0); hand = (sgn * 23.1, 24.7, -10)
        R = rx(a)
        rel = mv(R, [hand[i] - piv[i] for i in range(3)])
        comps.append((arm, torso, piv, mm(R, A0)))
        hp = tuple(piv[i] + rel[i] for i in range(3))
        HR = mm(R, H0)
        comps.append(("3820", head, hp, HR))
        if mic and sgn == -1:                              # Griff im Handloch (Loch lokal bei z = -10, Achse y)
            o = mv(HR, (0, -6, -10))
            comps.append(("90370", BLACK, tuple(hp[i] + o[i] for i in range(3)), HR))
    if hair is not None: comps.append(("3901", hair, (0, -24, 0), I3))
    for nm, col, off, Mi in comps:
        w = mv(M, off); pos = [P[0] + w[0], P[1] + w[1], P[2] + w[2]]
        leg = nm == "73200b-f1"
        add(Part(sub, nm, col, pos[0], pos[1], pos[2], rot, set(cells) if leg else set(), surf_y - 108 if leg else 0,
                 surf_y if leg else 0, studs=False,
                 extra=[f"1 {col} {fmt(pos[0])} {fmt(pos[1])} {fmt(pos[2])} {mstr(mm(M, Mi))} {nm}.dat"]))


# Kanye allein auf der Plattform, Blick nach vorne, Mikrofon in der rechten Hand
minifig("07_kanye", KANYE, Y_SURF, 0, DTAN, BLACK, RBROWN, hair=BLACK, arms=(-115, 0), mic=True)

# Publikum: Fans in dunkler Kleidung, Blick zur Plattform, unter der Buehne am dichtesten (Moshpit)
FAN_USED = set()
FANS = 0
SKIN = (LNOUGAT, MNOUGAT, NOUGAT, RBROWN, DBROWN)
def fan_ok(cells):
    for q in cells:
        if not (XMIN + 1 <= q[0] <= XMAX - 1 and ZMIN + 1 <= q[1] <= ZMAX - 1): return False
        for a in range(-2, 3):
            for b in range(-2, 3):
                n = (q[0] + a, q[1] + b)
                if n in TOWER_CELLS: return False
                if abs(a) <= 1 and abs(b) <= 1 and n in FAN_USED: return False
    return True


for x in range(XMIN + 1, XMAX - 1, 3):
    for z in range(ZMIN + 1, ZMAX - 1, 3):
        j = (math.sin(x * 12.9898 + z * 78.233) * 43758.5453) % 1.0
        x0, z0 = x + (1 if j > 0.66 else 0), z + (1 if 0.33 < j <= 0.66 else 0)
        dx, dz = x0 + 0.5, z0 + 0.5
        dist_ = max(0.0, max(abs(dx) - 8, abs(dz) - 6))              # Abstand zum Rand der Plattform (Grundriss)
        if j < min(0.55, dist_ / 36): continue                       # aussen lockerer
        if abs(dx) >= abs(dz): rot, cells = (90 if dx < 0 else 270), [(x0, z0), (x0, z0 + 1)]
        else: rot, cells = (180 if dz < 0 else 0), [(x0, z0), (x0 + 1, z0)]
        if not fan_ok(cells): continue
        u = (math.sin(x0 * 3.1 + z0 * 7.7) * 9173.3) % 1.0
        v = (math.sin(x0 * 5.3 + z0 * 2.9) * 5171.7) % 1.0
        near = dist_ < 6
        arms = (-165, -165) if u < (0.5 if near else 0.25) else ((-150, 0) if u < 0.6 else ((0, -140) if u < 0.75 else (0, 0)))
        torso = BLACK if v < 0.6 else (DBG if v < 0.8 else (WHITE if v < 0.9 else DTAN))
        legs = BLACK if v < 0.45 or v > 0.9 else (DBLUE if v < 0.75 else DBG)
        head = SKIN[int(u * 97) % len(SKIN)]
        hair = (BLACK, DBROWN, BLACK, RBROWN)[int(v * 31) % 4]
        minifig("08_publikum", cells, 0, rot, torso, legs, head, hair=hair, arms=arms)
        FAN_USED |= set(cells); FANS += 1
print("Fans:", FANS)

# ---------------- Grundplatte ----------------
add(Part("01_grundplatte", GROUND, BLACK, 0, 0, 0, 0, {(i, k) for i in range(XMIN, XMAX + 1) for k in range(ZMIN, ZMAX + 1)}, 0, 4, True))

TITLES = {"01_grundplatte": "Grundplatte 48x48 (Arena-Boden)", "02_tuerme": "Tuerme (Gittertuerme 95347)",
          "03_rig": "Lichtraster (Plattengitter und Haupttraeger)", "04_lichtraster": "Haengende Leuchten",
          "05_seile": "Seile 63142", "06_plattform": "Schwebende Plattform", "07_kanye": "Kanye",
          "08_publikum": "Publikum (Minifiguren)"}


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
    ground = {n for n, p in enumerate(parts) if p.name == GROUND}
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
    floating = [n for n in phys if parts[n].name != GROUND and not below[n] and not parts[n].hang]
    hanging_ok = [n for n in phys if not below[n] and parts[n].hang and above[n]]
    # Zell-Unterstuetzung (streng) nur als Info
    unsup_cells = 0
    for n in phys:
        p = parts[n]
        if p.name == GROUND or p.hang: continue
        for c in p.cells:
            if not idx_top.get((p.ybot, c)): unsup_cells += 1
    # Kollisionen (8-LDU-Slabs)
    occ = {}; coll = []
    for n in phys:
        p = parts[n]
        if p.name == GROUND: continue
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
    for p in parts:
        if not p.name.startswith("_"): bysub[p.sub] += p.lines()
    out = [f"0 FILE {NAME}.ldr", "0 Saint Pablo Tour - schwebende Buehne (LEGO MOC)", f"0 Name: {NAME}.ldr",
           "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""]
    for s in order: out += [f"0 // {TITLES.get(s, s)}", f"1 16 0 0 0 {ROT[0]} {s}.ldr"]
    out += ["0 NOFILE"]
    for s in order:
        out += [f"0 FILE {s}.ldr", f"0 {TITLES.get(s, s)}", f"0 Name: {s}.ldr"] + bysub[s] + ["0 NOFILE"]
    for fn, body in CUSTOM_FILES.items():
        out += [f"0 FILE {fn}", f"0 Name: {fn}"] + body + ["0 NOFILE"]
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f"{NAME}.mpd"), "w").write("\n".join(out) + "\n")
    bom = Counter((p.name, p.color) for p in parts if not p.name.startswith("_"))
    rows = ["LDraw Part,BrickLink ID,Name,Farbe,Menge"]; xml = ["<INVENTORY>"]
    for (nm, c), q in sorted(bom.items()):
        bl = BL_ID.get(nm, nm); cn, blc = COLORS[c]
        rows.append(f"{nm}.dat,{bl},\"{names.get(nm, nm)}\",{cn},{q}")
        xml.append(f"<ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID><COLOR>{blc}</COLOR><MINQTY>{q}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    open(os.path.join(OUT, f"{NAME}_bom.csv"), "w").write("\n".join(rows) + "\n")
    open(os.path.join(OUT, f"{NAME}_bricklink.xml"), "w").write("\n".join(xml) + "\n")
    print("TOTAL parts:", sum(bom.values()), "| Positionen:", len(bom))
    for s in order: print(f"  {s}: {sum(1 for p in parts if p.sub == s and not p.name.startswith(chr(95)))}")


bad = checks()
export()
print("CHECK", "OK" if bad == 0 else f"FEHLER ({bad})")

