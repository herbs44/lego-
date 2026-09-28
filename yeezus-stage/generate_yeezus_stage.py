"""
Yeezus Stage – LEGO MOC Generator
Mount Yeezus (Fels-Pyramide mit Grat und Wendelweg bis zum Gipfel), Buehnenpodest, Laufsteg mit Rampe,
Lower Stage (Felsplateau),
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
BL_ID = {"6141": "4073", "3815c01": "970c00", "63142": "x127c30pb01"}
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
# Koordinaten: Zellen x in [-32, 31], z in [-16, 15] (2 Baseplates 32x32 hintereinander).
# PUBLIKUMSSICHT (wie auf den Konzertfotos) = Blick von -x in Richtung +x: vorne die Lower Stage im
# Publikum, der Laufsteg fuehrt zum Berg, dahinter mittig der runde Screen. Von vorne gesehen liegt
# +z links. Die Ansichtszeichnung (Elevation) ist die Seitenansicht von +z.
COLORS.update({212: ("Bright Light Blue", 105)})
# Farbkonzept nach der 60-30-10-Regel, rein unbunt wie die Tour-Optik: Schwarz dominiert (Buehne, Screen),
# Weiss/Hellgrau fuer den Fels, Dunkelgrau fuer Risse, Schatten und Traverse.
XMIN, XMAX, ZMIN, ZMAX = -32, 31, -16, 15
GRID = [(i, k) for i in range(XMIN, XMAX + 1) for k in range(ZMIN, ZMAX + 1)]
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ROT_OUT = {(1, 0): 90, (-1, 0): 270, (0, 1): 180, (0, -1): 0}    # Slope-Gefaelle (Standard: nach -z)
rng = random.Random(11)

# ---------------- Hoehenfeld (in Steinhoehen) ----------------
PLAT = {(i, k) for i in range(3, 27) for k in range(-14, 14)}          # Buehnenpodest unter dem Berg
PLAT_H = 3
MREGION = {(i, k) for i in range(5, 26) for k in range(-13, 13)}       # Bereich des Bergs (vorne 2 Noppen Vorplatz)
RUNWAY = {(i, k) for i in range(-11, 3) for k in range(-2, 2)}          # Laufsteg (4 breit, mittig auf z = 0)
RUNWAY_H = 2
RAMP = {(i, k) for i in range(-14, -11) for k in range(-2, 2)}          # Rampe zur Lower Stage (Unterbau)
STAIR = {(i, 2) for i in range(-3, 0)} | {(i, -3) for i in range(-3, 0)}  # Stufen beidseitig am Laufsteg
STAGE_C, STAGE_R = (-22.0, 0.0), 8.6                                    # Lower Stage (Felsplateau)
STAGE_H = 4
APEX = (12.0, 0.0); APEX_H = 19
SUMMIT = {(11, -1), (12, -1), (11, 0), (12, 0)}                        # Gipfelplattform 2x2


def planes_height(p, apex, h0, faces):
    """konvexes Polyeder: h0 - max_i s_i * ((p - apex) . n_i)"""
    x, z = p
    m = max(s * ((x - apex[0]) * math.cos(math.radians(t)) + (z - apex[1]) * math.sin(math.radians(t)))
            for t, s in faces)
    return h0 - max(0.0, m)


# Berg wie auf den Fotos: unten ein Sockel mit zwei Weg-Ebenen, darauf eine spitze Pyramide. Nach vorne zeigt
# ein scharfer Grat, der gleichmaessig mit 2 Steinen pro Noppe steigt (durchgehend 65-Grad-Slopes). Nach hinten
# faellt ein langer, flacher Ruecken ab (Ansichtszeichnung). Um den Berg windet sich ein Wendelweg.
GRAT = 2 * math.sqrt(2)                   # Grat-Flanken: 2 Steine pro Noppe entlang x und z
PEAK = dict(apex=APEX, h0=APEX_H + 1.5, faces=[(135, GRAT), (225, GRAT), (90, 1.3), (270, 1.25), (0, 0.62)])
CRACKS = [[(13.5, 2.0), (15.5, 4.5)], [(14.0, -2.0), (16.0, -4.5)],     # Risse (Kerben) auf Flanken und Sockel,
          [(10.5, 5.5), (13.0, 8.0)], [(16.0, -6.5), (19.0, -7.5)],     # der Grat vorne bleibt glatt
          [(17.5, 5.0), (20.0, 7.5)]]

# Wendelweg: beginnt vorne rechts auf Podesthoehe und laeuft aussen rechts -> hinten -> links nach oben,
# vorne als Sims vor dem Grat entlang, dann eine Ebene hoeher rechts und hinten herum und als Gipfeltreppe
# ueber den flachen Ruecken zur Spitze. Station = 2 Zellen quer zum Weg (talseitig, bergseitig).
WAY_SEGS = [("A", [((x, -12), (x, -11)) for x in range(5, 23)], 3.0, 5.0),
            ("B", [((24, z), (23, z)) for z in range(-12, 12)], 5.0, 7.0),
            ("C", [((x, 11), (x, 10)) for x in range(22, 7, -1)], 7.0, 8.67),
            ("D", [((6, z), (7, z)) for z in range(11, -9, -1)], 8.67, 10.0),
            ("E", [((x, -10), (x, -9)) for x in range(6, 21)], 10.0, 13.33),
            ("F", [((22, z), (21, z)) for z in range(-10, 1)], 13.33, 14.33),
            ("G", [((x, -1), (x, 0)) for x in range(20, 12, -1)], 14.33, APEX_H)]
INSIDE = {(x, z) for x in range(8, 23) for z in range(-10, 10)}        # Sockel innerhalb des aeusseren Umlaufs
STATIONS = []                   # (Abschnitt, Zellen (aussen, innen), Hoehe in Platten)
for seg, sts, h0, h1 in WAY_SEGS:
    n = len(sts)
    for j, cells in enumerate(sts):
        t = (j + 1) / n if seg == "G" else j / n
        STATIONS.append((seg, cells, int(math.floor((h0 + (h1 - h0) * t) * 3 + 0.5))))
WAY = {}                        # Zelle -> (Abschnitt, Hoehe in Platten)
for seg, cells, hp in STATIONS:
    for c in cells: WAY[c] = (seg, hp)
assert len(WAY) == 2 * len(STATIONS)


def seg_dist(p, a, b):
    ax, az = a; bx, bz = b; px, pz = p
    dx, dz = bx - ax, bz - az; L = dx * dx + dz * dz
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L)) if L else 0.0
    return math.hypot(px - ax - t * dx, pz - az - t * dz)


def crack_d(p, cracks=CRACKS):
    return min(seg_dist(p, a, b) for poly in cracks for a, b in zip(poly, poly[1:]))


def mountain_f(p):
    """kontinuierliche Berghoehe (Steine) ueber dem Podest"""
    return min(APEX_H + 0.4, planes_height(p, PEAK["apex"], PEAK["h0"], PEAK["faces"]))


def stage_f(p):
    """Lower Stage: Felsplateau mit unregelmaessigem Rand und steilen Felswaenden"""
    x, z = p[0] - STAGE_C[0], p[1] - STAGE_C[1]
    a = math.atan2(z, x)
    r = STAGE_R * (1 + 0.10 * math.sin(3 * a + 0.7) + 0.06 * math.sin(7 * a + 2.1) + 0.04 * math.sin(11 * a))
    edge = r - math.hypot(x, z * 1.08)
    return STAGE_H * max(0.0, min(1.0, 0.25 + edge / 2.2))


# Ecktuerme: vorne je 1 Gittertraeger (freie Sicht), hinten hinter dem Screen je 2 nebeneinander
TOWERS = [(-31, -15), (-31, 15)] + [(31, Z) for Z in (-15, -13, 13, 15)]   # vorne 1, hinten 2 Traeger je Ecke
RESERVED = {(X + a, Z + b) for X, Z in TOWERS for a in (-1, 0) for b in (-1, 0)}
def vnoise(x, z, sc=3.0, seed=0):
    """glatte Werte-Rauschfunktion 0..1"""
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx
    b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


# Fels neben dem Weg: bergseitig mindestens 1 Stein hoeher als der Weg (Wand), talseitig hoechstens auf
# Weghoehe (der Weg ist in die Flanke geschnitten). Die Gipfeltreppe liegt auf dem Hang.
def natural(c):
    """Fels innerhalb des aeusseren Umlaufs: Pyramide, mindestens auf Sockelhoehe"""
    p = (c[0] + 0.5, c[1] + 0.5)
    hm = round(mountain_f(p), 6)
    tier = 9 + (vnoise(p[0], p[1], 2.5, 6) - 0.5) * 1.4                # niedriger Sockel, Pyramide dominiert
    h = int(math.floor(max(hm, tier) + 0.5))
    if crack_d(p) < 0.5: h -= 1                        # Risse als Kerben
    return min(APEX_H, h)


REQ, CAP = defaultdict(int), {}
for seg, (co, ci), hp in STATIONS:
    if seg == "G": continue
    out = (co[0] - ci[0], co[1] - ci[1])                  # talseitige Richtung
    for q in (co, ci):
        for a, b in N8:
            n = (q[0] + a, q[1] + b)
            if n not in MREGION or n in WAY: continue
            side = a * out[0] + b * out[1]
            if side == 0: side = -1 if mountain_f((n[0] + 0.5, n[1] + 0.5)) > hp / 3 + 0.5 else 1
            if side < 0:
                if a == 0 or b == 0: REQ[n] = max(REQ[n], hp // 3 + 1)
            else: CAP[n] = min(CAP.get(n, 99), hp // 3)
        for k in (2, 3):                                    # bergseitig eine Schulter statt einer Rinne
            n = (q[0] - k * out[0], q[1] - k * out[1])
            if n in MREGION and n not in WAY: REQ[n] = max(REQ[n], hp // 3 + 1)
HF, MAT = {}, {}
for c in GRID:
    if c in RESERVED: continue
    p = (c[0] + 0.5, c[1] + 0.5)
    h, m = 0, None
    if c in PLAT:
        h, m = PLAT_H, "podest"
        if c in WAY: h, m = WAY[c][1] // 3, "weg"
        elif c in MREGION:
            if c in INSIDE: h = min(max(REQ[c], natural(c)), CAP.get(c, 99))   # talseitig hat Vorrang
            else: h = CAP.get(c, PLAT_H + 1) - 1 - (vnoise(p[0], p[1], 2.0, 4) > 0.6)   # Fuss aussen, unruhig
            h, m = (h, "berg") if h > PLAT_H else (PLAT_H, "podest")
    elif c in RUNWAY: h, m = RUNWAY_H, "laufsteg"
    elif c in RAMP: h, m = RUNWAY_H + 1, "rampe"
    elif c in STAIR: h, m = 1, "laufsteg"
    else:
        hs = stage_f(p)
        if hs > 0.5: h, m = int(round(hs)), "fels"
    if h: HF[c], MAT[c] = h, m
# Mulden im Fels schliessen (Zelle tiefer als alle 4 Nachbarn), damit hinter Wegkanten keine Loecher entstehen
for _ in range(4):
    for c in sorted(INSIDE):
        if MAT.get(c) != "berg": continue
        nb = [HF.get((c[0] + a, c[1] + b), 0) for a, b in DIRS]
        if min(nb) > HF[c]: HF[c] = min(nb)
# Gipfelplattform 2x2
for c in SUMMIT: HF[c], MAT[c] = APEX_H, "berg"
# Rampe: die Lower Stage beginnt direkt dahinter auf voller Hoehe
RAMP_TOP = [(-15, z) for z in range(-2, 2)]
for c in RAMP_TOP: HF[c], MAT[c] = STAGE_H, "fels"
GMAX = max(HF.values())
S = [{c for c, h in HF.items() if h > g} for g in range(GMAX + 1)]

# Rockwork-Ueberhaenge: die oberste Lage der Lower Stage kragt stellenweise 1 Noppe aus, darunter sitzt
# ein umgedrehter 45-Grad-Slope (3665). Verteilung ueber Rauschen statt Muster.
def _vn(x, z, sc, seed):
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx
    b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


LIPS = []                       # (Zelle innen, Zelle aussen, Richtung) - umgedrehter Slope in Lage STAGE_H-2
_gl = STAGE_H - 1               # Lage, die auskragt
_used = set()
for c in sorted(S[_gl]):
    if MAT[c] != "fels" or c not in S[_gl - 1]: continue
    if _vn(c[0] + 0.5, c[1] + 0.5, 2.2, 9) < 0.45: continue
    for d in DIRS:
        o = (c[0] + d[0], c[1] + d[1])
        if o in S[_gl - 1] or o in RESERVED or o in _used or o in RUNWAY or o in RAMP: continue
        if not (XMIN <= o[0] <= XMAX and ZMIN <= o[1] <= ZMAX): continue
        if any((o[0] + a, o[1] + b) in RAMP | RUNWAY for a, b in N8): continue
        LIPS.append((c, o, d)); _used.add(o); break
for (c, o, d) in LIPS:
    HF.setdefault(o, STAGE_H); MAT[o] = "fels"
    S[_gl].add(o)
LIP_OUT = {o for _, o, _ in LIPS}


def grad_dirs(c):
    """Richtungen nach Gefaelle sortiert (staerkstes Gefaelle zuerst)"""
    p = (c[0] + 0.5, c[1] + 0.5)
    f = mountain_f if MAT.get(c) in ("berg", "podest", "weg") else stage_f
    g = [(f((p[0] + d[0] * 0.7, p[1] + d[1] * 0.7)) - f(p), d) for d in DIRS]
    g.sort()
    return [d for _, d in g]


# ---------------- Rock-Farben ----------------
SUN = (-0.75, 0.8, 0.3)   # Licht von vorne (-x) oben, etwas von links
def rock_color(c, top=False, g=None):
    if MAT.get(c) == "berg" and crack_d((c[0] + 0.5, c[1] + 0.5)) < 0.75: return DBG
    if MAT.get(c) == "fels" and crack_d((c[0] + 0.5, c[1] + 0.5), STAGE_CRACKS) < 0.6: return DBG
    if top:
        v = vnoise(c[0] + 0.5, c[1] + 0.5, 3.2, 1 if MAT.get(c) == "fels" else 2)
        if MAT.get(c) == "fels": return WHITE if v > 0.62 else LBG
        return LBG if v > 0.68 else WHITE
    p = (c[0] + 0.5, c[1] + 0.5)
    f = mountain_f if MAT.get(c) in ("berg", "weg") else stage_f
    gx = f((p[0] + 0.5, p[1])) - f((p[0] - 0.5, p[1])); gz = f((p[0], p[1] + 0.5)) - f((p[0], p[1] - 0.5))
    n = (-gx, 1.0, -gz); L = math.sqrt(sum(v * v for v in n))
    shade = sum(a * b for a, b in zip(n, SUN)) / L
    shade -= 0.3 * (vnoise(c[0] + 0.5, c[1] + 0.5, 2.5, 3) > 0.72)
    if g is not None and MAT.get(c) in ("berg", "weg"):
        shade += 0.35 * (g / APEX_H - 0.45)          # Verlauf: Spitze im Licht, Fuss im Schatten
        if shade < 0.12: return DBG
    return WHITE if shade > 0.55 else LBG


STAGE_CRACKS = [[(-28.0, -3.0), (-24.0, -1.0), (-21.0, 2.5), (-17.0, 3.0)],
                [(-24.0, -1.0), (-23.0, -5.5)], [(-19.0, -6.0), (-16.5, -2.0)]]
ROCK = ("berg", "fels")
SLOPE_OK = ("berg", "fels")

SNOT_LINKS = []           # (Anbauteil, Halter) - seitliche Verbindungen, die der Check als Verbindung wertet
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
    deck[g] = {c for c in exposed if dist[c] > T_SHELL + 1 and MAT[c] not in ("laufsteg", "weg")}
    solid[g] = {c for c in Sg if dist[c] <= T_SHELL or c in exposed} - deck[g]
    for c in deck[g]:
        if c[0] % 4 == 0 and c[1] % 4 == 0:
            blk = {(c[0] + a, c[1] + b) for a in (0, 1) for b in (0, 1)}
            if blk <= deck[g]: pillars[g] |= blk
for g in range(GMAX, 0, -1):          # Stuetz-Propagation: alles braucht etwas darunter
    solid[g - 1] |= (solid[g] | pillars[g]) - (LIP_OUT if g == _gl else set())   # Ueberhang: Stuetze = umgedr. Slope
    deck[g - 1] -= solid[g - 1]

# ---------------- Rundung: Slopes an Stufenkanten ----------------
STEP_PART = {1: "3040b", 2: "4286", 3: "60477"}          # 45 / 33 / 18 Grad, Hoehe 1 Stein
STEEP_PART = {2: "60481", 3: "4460b"}                    # 65 / 75 Grad, Hoehe 2 / 3 Steine
replaced = set()     # (Zelle, Lage) - Stein durch Slope ersetzt
covered = set()      # (Zelle, Lage) - von Slope-Schraege belegt
SLOPES = []          # (Teil, Zelle, Richtung, Lage unten, Hoehe, Zellen)
# Rampe Laufsteg -> Lower Stage (wie in der Ansichtszeichnung): zwei 18-Grad-Slopes 4x1 hintereinander
# ergeben eine durchgehende, gleichmaessige Steigung ueber 6 Noppen
RAMP_SLOPES = set()
for z in range(-2, 2):
    for c, g in (((-12, z), RUNWAY_H), ((-15, z), RUNWAY_H + 1)):
        cells = [c] + [(c[0] + i, z) for i in (1, 2, 3)]
        SLOPES.append(("60477", c, (1, 0), g, 1, cells)); RAMP_SLOPES.add(c)
        replaced.add((c, g))
        for q in cells[1:]: covered.add((q, g))
for (c, o, d) in LIPS:                         # umgedrehte Slopes unter den Ueberhaengen
    replaced.add((c, _gl - 1)); covered.add((o, _gl - 1))
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
                    and MAT.get(q) != "weg" \
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
        return rock_color(c, g=g) if vis else BLACK
    if m == "rampe": return BLACK
    if m == "weg":
        # Felswand unter dem Wendelweg: senkrechte Riefen wie auf den Fotos. Der Farbton haengt nur von der
        # Position entlang der Wand ab (nicht von der Lage), unten dunkler (Schatten am Fuss).
        if not side_visible(c, g): return BLACK
        u = (math.sin((c[0] * 3 + c[1] * 5) * 12.9898) * 43758.5453) % 1.0
        base = LBG if u < 0.5 else WHITE if u < 0.85 else DBG
        return DBG if g < PLAT_H + 1 and base != WHITE else base
    # Podest / Laufsteg: schwarz, sichtbare Fugen dunkelgrau (Paneele)
    return BLACK


def sub_of(c):
    return {"podest": "02_podest", "berg": "03_berg", "laufsteg": "04_laufsteg", "rampe": "04_laufsteg",
            "fels": "05_lower_stage", "weg": "03_berg"}[MAT[c]]


# Front-Fills: in der obersten Podestlage vorne Steine 1x2 mit Seitennoppen, darauf Gitter-Fliesen (SNOT)
PX0 = min(p[0] for p in PLAT)
FRONTFILL = [((PX0, z0), (PX0, z0 + 1)) for z0 in (-12, -8, 6, 10)]
for pair in FRONTFILL:
    for c in pair:
        assert c in solid[PLAT_H - 1] and MAT[c] == "podest"
        replaced.add((c, PLAT_H - 1))
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

for (a, b) in FRONTFILL:
    y = -BH * PLAT_H
    front = add(Part("02_podest", "11211", BLACK, ctr(a[0]), y, (b[1]) * LDU, 270, {a, b}, y, y + BH))
    grille = add(Part("02_podest", "2412b", DBG, ctr(a[0]) - 18, y + 10, b[1] * LDU, 0,
                      {(a[0] - 1, a[1]), (b[0] - 1, b[1])}, y, y + 20, studs=False, hang=True,
                      extra=[f"1 {DBG} {fmt(ctr(a[0]) - 18)} {fmt(y + 10)} {fmt(b[1] * LDU)} 0 1 0 0 0 -1 -1 0 0 2412b.dat"]))
    SNOT_LINKS.append((grille, front))
for (c, o, d) in LIPS:
    y = -BH * _gl
    add(Part(sub_of(c), "3665a", rock_color(c, g=_gl - 1), ctr(c[0]), y, ctr(c[1]), ROT_OUT[d], [c, o], y, y + BH,
             studs=True, studcells={c, o}))
for (name, c, d, g, h, cells) in SLOPES:
    y = -BH * (g + h)
    col = DBG if c in RAMP_SLOPES else rock_color(c, g=g) if MAT[c] in ROCK else BLACK
    add(Part(sub_of(c), name, col, ctr(c[0]), y, ctr(c[1]), ROT_OUT[d], cells, y, y + BH * h,
             studs=True, studcells={c}))

# Abdeckung aller noch offenen Oberseiten.
# Felskanten: Mischung aus gebogenen Slopes 2x1 (11477, "ausgewaschen") und Cheese-Slopes 1x1 (Rockwork-Tipp:
# gebogene Keile fuer weiche, erodierte Uebergaenge), sonst Fliesen. Laufsteg: Dielen im Verband.
caps = defaultdict(dict)
PLANKS = defaultdict(set)
for g in range(GMAX + 1):
    Sa = S[g + 1] if g + 1 <= GMAX else set()
    y = -BH * (g + 1)
    open_ = sorted(c for c in S[g] - Sa if (c, g + 1) not in covered and (c, g) not in replaced)
    openset, done = set(open_), set()
    # Pass 1: gebogene Slopes auf Randzelle + Nachbar innen
    for c in open_:
        if MAT[c] not in ROCK or c in SUMMIT or c in done: continue
        drop = [d for d in grad_dirs(c) if (c[0] + d[0], c[1] + d[1]) not in S[g]]
        if not drop or vnoise(c[0] + 0.5, c[1] + 0.5, 2.3, 11) < 0.5: continue
        d = drop[0]; i = (c[0] - d[0], c[1] - d[1])
        if i not in openset or i in done or MAT.get(i) not in ROCK or i in SUMMIT: continue
        col = rock_color(c, top=True)
        add(Part(sub_of(c), "11477", col, (ctr(c[0]) + ctr(i[0])) / 2, y, (ctr(c[1]) + ctr(i[1])) / 2, ROT_OUT[d],
                 {c, i}, y - 16, y, studs=False))
        done |= {c, i}
    # Pass 2: Rest
    for c in open_:
        if c in done: continue
        m = MAT[c]
        if c in SUMMIT: caps[(g, "03_berg")][c] = BLACK; continue
        if m in ROCK:
            drop = [d for d in grad_dirs(c) if (c[0] + d[0], c[1] + d[1]) not in S[g]]
            if drop and vnoise(c[0] + 0.5, c[1] + 0.5, 1.7, 8) < 0.78:
                add(Part(sub_of(c), "54200", rock_color(c, top=True), ctr(c[0]), y, ctr(c[1]), ROT_OUT[drop[0]],
                         {c}, y - 16, y, studs=False))
                continue
            caps[(g, sub_of(c))][c] = rock_color(c, top=True)
        elif m == "rampe": caps[(g, sub_of(c))][c] = DBG
        elif m == "podest":
            edge = any((c[0] + a, c[1] + b) not in S[g] for a, b in DIRS)
            caps[(g, sub_of(c))][c] = DBG if edge else BLACK
        elif m == "laufsteg": PLANKS[g].add(c)
        elif m == "weg": continue                              # Wendelweg: eigene Oberflaeche (unten)
        else: caps[(g, sub_of(c))][c] = DBG
for (g, sb), cc in caps.items():
    plates(sb, cc, -BH * (g + 1) - PH, g % 2, table=TILE, studs=False)
# Dielen: 1 Noppe breite Fliesen entlang x, Stoesse von Reihe zu Reihe versetzt (Verband)
TILE_LEN = {1: "3070b", 2: "3069b", 4: "2431", 6: "6636", 8: "4162"}
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
                rest = len(run) - pos
                n = min(first, rest) if pos == 0 else min(4, rest)
                while n not in TILE_LEN: n -= 1
                seg = run[pos:pos + n]; pos += n
                cx = sum(ctr(x) for x in seg) / n
                add(Part("04_laufsteg", TILE_LEN[n], DBG, cx, y, ctr(z), 0, {(x, z) for x in seg}, y, y + PH, studs=False))

# Wendelweg-Oberflaeche: Stationen gleicher Hoehe bilden einen Absatz. Jede Stufe ist 1 Platte hoch
# (dunkelgraue Platten als Setzstufe, weisse Fliesen als Trittflaeche - so liest man die Stufen auch
# aus der Entfernung). Im Aussenrand laengerer Absaetze sitzen Bodenleuchten (Gitter-Fliese 1x2).
TILE_LEN[3] = "63864"
WAY_GROUPS = []
for seg, cells, hp in STATIONS:
    if WAY_GROUPS and WAY_GROUPS[-1][0] == seg and WAY_GROUPS[-1][2] == hp: WAY_GROUPS[-1][1].append(cells)
    else: WAY_GROUPS.append([seg, [cells], hp])
N_LIGHTS = 0


def row_tiles(sub, row, y, color, lengths=(4, 3, 2, 1)):
    """1 Noppe breite Fliesen entlang einer Zellreihe (Zellen in Wegrichtung sortiert)"""
    pos = 0
    while pos < len(row):
        n = next(L for L in lengths if L <= len(row) - pos)
        seg = row[pos:pos + n]; pos += n
        along_x = len({q[0] for q in seg}) == n
        cx = sum(ctr(q[0]) for q in seg) / n; cz = sum(ctr(q[1]) for q in seg) / n
        add(Part(sub, TILE_LEN[n], color, cx, y, cz, 0 if along_x else 90, set(seg), y, y + PH, studs=False))


for seg, sts, hp in WAY_GROUPS:
    base = -BH * (hp // 3); k = hp % 3
    allc = {c for st in sts for c in st}
    for i in range(k):
        plates("06_wendelweg", {c: DBG for c in allc}, base - (i + 1) * PH, i % 2)
    y = base - (k + 1) * PH
    for r in (0, 1):
        row = [st[r] for st in sts]
        if r == 0 and seg != "G" and len(row) >= 4:           # Bodenleuchte mittig im Aussenrand
            m = len(row) // 2 - 1
            lamp = row[m:m + 2]
            along_x = lamp[0][0] != lamp[1][0]
            add(Part("06_wendelweg", "2412b", DBG, sum(ctr(q[0]) for q in lamp) / 2, y, sum(ctr(q[1]) for q in lamp) / 2,
                     0 if along_x else 90, set(lamp), y, y + PH, studs=False))
            N_LIGHTS += 1
            row_tiles("06_wendelweg", row[:m], y, WHITE); row_tiles("06_wendelweg", row[m + 2:], y, WHITE)
        else:
            row_tiles("06_wendelweg", row, y, WHITE)
print("Wendelweg:", len(STATIONS), "Stationen,", len(WAY_GROUPS), "Absaetze,", N_LIGHTS, "Bodenleuchten,",
      "Hoehe", STATIONS[0][2] / 3, "->", STATIONS[-1][2] / 3, "Steine")

# ---------------- Runder Screen hinter dem Berg (zeigt zum Publikum, -x) ----------------
SCR_X = (27, 28, 29)                         # vorne .. hinten; hinten schwarze Rueckwand
DISC_ZC, DISC_RZ = 0.0, 14.0                 # Mitte zwischen z=-1 und z=0, Radius 14 Noppen
DISC_RC, DISC_RY = 20.0, 10.3                # Mitte (Steinlagen) und Radius in Lagen


def disc_row(r):
    v = (r + 0.5 - DISC_RC) / DISC_RY
    if abs(v) > 1: return []
    hw = math.sqrt(1 - v * v) * DISC_RZ
    return [z for z in range(ZMIN, ZMAX + 1) if abs(z + 0.5 - DISC_ZC) <= hw]


def sky(z, r):
    """dunkler Sturmhimmel wie auf den Fotos: heller Sichelrand links (von vorne: +z = links),
    Wolkenband von oben rechts zur Mitte, sonst schwarz/dunkelgrau"""
    u = (z + 0.5 - DISC_ZC) / DISC_RZ; v = (r + 0.5 - DISC_RC) / DISC_RY
    rho = math.hypot(u, v)
    ang = math.degrees(math.atan2(-v, u))                   # 0 = links, +90 = unten (von vorne)
    if rho > 0.86 and -45 < ang < 70: return WHITE           # Sichel
    if rho > 0.77 and -25 < ang < 50: return LBG
    band = 1 - abs((v - 0.3) - 0.45 * (-u)) / 0.5
    n = vnoise(z + 0.5, (r + 0.5) * 1.4, 4.0, 5) * 0.65 + vnoise(z + 0.5, (r + 0.5) * 1.4, 2.0, 6) * 0.35
    c = 0.6 * n + 0.45 * max(0.0, band)
    if c > 0.80: return WHITE
    if c > 0.66: return LBG
    if c > 0.52: return DBG
    return BLACK


DISC_ROWS = {r: disc_row(r) for r in range(0, 40) if disc_row(r)}
R0 = min(DISC_ROWS)
SIZES = [1, 2, 3, 4, 6, 8]


def partition(L, left_need, right_need, prev_joints, colors=None):
    """Lauf der Laenge L in Steinlaengen zerlegen: Endsteine reichen auf gestuetzte Zellen,
    Fugen moeglichst versetzt zur Lage darunter (Verband)"""
    INF = 10 ** 9
    best = [INF] * (L + 1); back = [None] * (L + 1); best[0] = 0
    for pos in range(L):
        if best[pos] == INF: continue
        for s_ in SIZES:
            e = pos + s_
            if e > L: continue
            if pos == 0 and s_ < left_need: continue
            if e == L and s_ < right_need: continue
            cost = best[pos] + 1 + (3 if e < L and e in prev_joints else 0)
            if colors:
                seg = colors[pos:e]; cost += 2.5 * (len(seg) - Counter(seg).most_common(1)[0][1])
            if cost < best[e]: best[e] = cost; back[e] = pos
    out, e = [], L
    while e > 0: out.append(e - back[e]); e = back[e]
    return out[::-1]


PED_Z = DISC_ROWS[R0]
for g in range(R0):                                            # Sockel (hinter dem Berg verborgen)
    bricks("07_screen", {(x, z): BLACK for x in SCR_X for z in PED_Z}, g)
prev_cells = set(PED_Z); prev_j = defaultdict(set)
for r, zs in sorted(DISC_ROWS.items()):
    bands = [(29,), (28, 27)] if r % 2 == 0 else [(29, 28), (27,)]
    joints_here = set()
    for band in bands:
        run = list(zs); sup = [z for z in run if z in prev_cells]
        left_need = (sup[0] - run[0] + 1) if sup else 1
        right_need = (run[-1] - sup[-1] + 1) if sup else 1
        pj = {z - run[0] for x in band for z in prev_j[x]}
        pos = 0
        cols = [sky(z, r) for z in run] if 27 in band else None
        for s_ in partition(len(run), left_need, right_need, pj, cols):
            seg = run[pos:pos + s_]; pos += s_
            joints_here.add(seg[-1] + 1)
            col = Counter(sky(z, r) for z in seg).most_common(1)[0][0] if 27 in band else BLACK
            w = len(band)
            cells = [(x, z) for x in band for z in seg]
            cx = sum(ctr(q[0]) for q in cells) / len(cells); cz = sum(ctr(q[1]) for q in cells) / len(cells)
            add(Part("07_screen", BRICK[(min(w, s_), max(w, s_))], col, cx, -BH * (r + 1), cz,
                     90 if s_ > w else 0, cells, -BH * (r + 1), -BH * r))
        for x in band: prev_j[x] = set(joints_here)
    prev_cells = set(zs)
DISC_TOP = max(DISC_ROWS)
# Runde Formen: Jede Zeile der oberen Haelfte ist schmaler als die darunter. Auf die freien Stufenenden
# kommen gebogene Slopes (2 Zellen) bzw. Cheese-Slopes (1 Zelle), Gefaelle nach aussen; von vorne wird
# der Umriss dadurch rund statt treppig. Vorn in Bildfarbe, dahinter schwarz.
TIE_CELLS = {(29, z) for z in (-1, 0)}
for r in sorted(DISC_ROWS):
    here, above = DISC_ROWS[r], set(DISC_ROWS.get(r + 1, []))
    exposed = [z for z in here if z not in above]
    if not exposed: continue
    y = -BH * (r + 1)
    ends = []
    lo = [z for z in exposed if not above or z < min(above)]
    hi = [z for z in exposed if above and z > max(above)]
    if not above: lo, hi = exposed[:len(exposed) // 2], exposed[len(exposed) // 2:]
    for grp, d in ((lo, (0, -1)), (sorted(hi, reverse=True), (0, 1))):
        grp = sorted(grp, key=lambda z: -z * d[1])          # von aussen nach innen
        for x in SCR_X:
            col = sky(grp[0], r) if (x == 27 and grp) else BLACK
            k = 0
            if len(grp) >= 2 and (x, grp[0]) not in TIE_CELLS and (x, grp[1]) not in TIE_CELLS:
                add(Part("07_screen", "11477", col, ctr(x), y, (ctr(grp[0]) + ctr(grp[1])) / 2, ROT_OUT[d],
                         {(x, grp[0]), (x, grp[1])}, y - 16, y, studs=False)); k = 2
            elif grp and (x, grp[0]) not in TIE_CELLS:
                add(Part("07_screen", "54200", col, ctr(x), y, ctr(grp[0]), ROT_OUT[d], {(x, grp[0])}, y - 16, y,
                         studs=False)); k = 1
            rest = {(x, z): BLACK for z in grp[k:] if (x, z) not in TIE_CELLS}
            if rest: plates("07_screen", rest, y - PH, 0, table=TILE, studs=False)

# ---------------- Ecktuerme und Traversen-Rechteck ----------------
TRUSS_Y = -BH * 3 - 3 * 240 - 2 * PH       # Unterkante Traverse (= Oberkante Tuerme)
for side in {(1 if X > 0 else -1, 1 if Z > 0 else -1) for X, Z in TOWERS}:
    grp = [(X, Z) for X, Z in TOWERS if (1 if X > 0 else -1, 1 if Z > 0 else -1) == side]
    base = {(X + a, Z + b) for X, Z in grp for a in (-1, 0) for b in (-1, 0)}
    for g in range(3):
        pack("08_traverse", {c: BLACK for c in base}, BRICK, -BH * (g + 1), BH, g % 2)
    yy = -BH * 3
    for k in range(3):
        yy -= 240
        for X, Z in grp:
            cells = {(X - 1, Z - 1), (X, Z - 1), (X - 1, Z), (X, Z)}
            add(Part("08_traverse", "95347", DBG, X * LDU, yy, Z * LDU, 0 if X < 0 else 180, cells, yy, yy + 240))
        if k < 2:
            yy -= PH
            plates("08_traverse", {c: DBG for c in base}, yy, 1)
assert yy == TRUSS_Y
RING = {(i, k) for i in range(XMIN, XMAX + 1) for k in (-16, -15, 14, 15)} | \
       {(i, k) for i in (-32, -31, 29, 30, 31) for k in range(ZMIN, ZMAX + 1)}
# Verbindung Screen-Oberkante -> hintere Traverse (haelt den Screen oben): Steine + Platten auf der Rueckwand
TIE = [(29, z) for z in DISC_ROWS[DISC_TOP] if -1 <= z <= 0]
gap = -BH * (DISC_TOP + 1) - TRUSS_Y
yy = -BH * (DISC_TOP + 1)
while gap >= BH:
    pack("07_screen", {c: BLACK for c in TIE}, BRICK, yy - BH, BH, 0); yy -= BH; gap -= BH
while gap >= PH:
    plates("07_screen", {c: BLACK for c in TIE}, yy - PH, 0); yy -= PH; gap -= PH
assert yy == TRUSS_Y and gap == 0
y = TRUSS_Y - PH
t1 = plates("08_traverse", {c: DBG for c in RING}, y, 0)
for p in t1:
    if not (p.cells & (RESERVED | set(TIE))): p.hang = True
t2, nc = bond_layer("08_traverse", RING, t1, y - PH, DBG)
assert nc == 1
y -= PH
POSTS = set()
for i in range(XMIN, XMAX + 1, 3):
    POSTS |= {(i, -16 if (i // 3) % 2 == 0 else -15), (i, 15 if (i // 3) % 2 == 0 else 14)}
for k in range(ZMIN, ZMAX + 1, 3):
    POSTS |= {(-32 if (k // 3) % 2 == 0 else -31, k), (31 if (k // 3) % 2 == 0 else 29, k)}
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


SLING_LINKS = SNOT_LINKS  # seitliche Verbindungen (SNOT), die der Check als Verbindung wertet
# Line-Arrays links und rechts vom Berg (wie PA-Anlagen), unten J-foermig zum Publikum (-x)
ARRAYS = [(10, -15), (17, -15), (10, 15), (17, 15)]       # Gitterpunkt (Mitte 2x2) unter der Seitentraverse
for ax, az in ARRAYS:
    J_OFF = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4]
    while True:                                          # Laenge: mind. 2 Steine Luft ueber allem darunter
        yy = TRUSS_Y + PH; ok = True
        for k, off in enumerate(J_OFF):
            cz = {(ax - off + a, az + b) for a in (-1, 0) for b in (-1, 0)}
            yy += BH + (PH if k < len(J_OFF) - 1 else 0)
            if yy > top_y(cz) - 2 * BH: ok = False; break
        if ok: break
        J_OFF = J_OFF[:3] + J_OFF[4:]
    yy = TRUSS_Y
    add(Part("09_line_arrays", "3022", DBG, ax * LDU, yy, az * LDU, 0, {(ax + a, az + b) for a in (-1, 0) for b in (-1, 0)},
             yy, yy + PH, hang=True))
    yy += PH
    for k, off in enumerate(J_OFF):
        cells = {(ax - off + a, az + b) for a in (-1, 0) for b in (-1, 0)}
        # Box = Stein 1x2 mit 2 Seitennoppen (vorne, Noppen zum Publikum) + Stein 1x2 dahinter;
        # auf den Seitennoppen sitzt ein Gitter-Fliese 1x2 (SNOT) als Lautsprecherfront
        fx = ax - off - 1                                 # vordere Spalte (-x)
        front = add(Part("09_line_arrays", "11211", BLACK, ctr(fx), yy, az * LDU, 270, {(fx, az - 1), (fx, az)},
                         yy, yy + BH, hang=True))
        add(Part("09_line_arrays", "3004", BLACK, ctr(fx + 1), yy, az * LDU, 90, {(fx + 1, az - 1), (fx + 1, az)},
                 yy, yy + BH, hang=True))
        grille = add(Part("09_line_arrays", "2412b", DBG, ctr(fx) - 18, yy + 10, az * LDU, 0,
                          {(fx - 1, az - 1), (fx - 1, az)}, yy, yy + 20, studs=False, hang=True,
                          extra=[f"1 {DBG} {fmt(ctr(fx) - 18)} {fmt(yy + 10)} {fmt(az * LDU)} 0 1 0 0 0 -1 -1 0 0 2412b.dat"]))
        SLING_LINKS.append((grille, front))
        yy += BH
        if k < len(J_OFF) - 1:
            no = J_OFF[k + 1]
            pc = {(ax - no + a, az + b) for a in (-1, 0) for b in (-1, 0)}
            add(Part("09_line_arrays", "3022", DBG, (ax - no) * LDU, yy, az * LDU, 0, pc, yy, yy + PH, hang=True))
            yy += PH

# Moving Heads: an den Seitentraversen ueber der Lower Stage und an der vorderen Traverse
HEADS = [(x, z) for x in (-28, -22, -16) for z in (-16, 14)] + [(-32, z) for z in (-6, 4)]
for hx, hz in HEADS:
    cells = {(hx + a, hz + b) for a in (0, 1) for b in (0, 1)}
    yy = TRUSS_Y
    for name, col, h in (("3022", BLACK, PH), ("3941", BLACK, BH), ("4032a", TCLEAR, PH)):
        add(Part("10_licht", name, col, (hx + 1) * LDU, yy, (hz + 1) * LDU, 0, cells, yy, yy + h, hang=True))
        yy += h

# Grundplatten
for sx in (-1, 1):
    cells = {(i, k) for i in (range(0, 32) if sx > 0 else range(-32, 0)) for k in range(-16, 16)}
    add(Part("01_baseplates", "3811", BLACK, sx * 320, 0, 0, 0, cells, 0, 4, True))

TITLES = {"01_baseplates": "Grundplatten (2x 32x32)", "02_podest": "Buehnenpodest", "03_berg": "Mount Yeezus",
          "04_laufsteg": "Laufsteg mit Rampe", "05_lower_stage": "Lower Stage (Felsplateau)",
          "06_wendelweg": "Wendelweg (Spiralpfad zum Gipfel)",
          "07_screen": "Runder Screen (hinter dem Berg)", "08_traverse": "Ecktuerme und Traversen-Rechteck", "09_line_arrays": "Line-Arrays",
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
