"""
Travis Scott – UTOPIA – Circus Maximus Tour – MetLife Stadium, 09.10.2024 ("One Night Only in Utopia")
LEGO-MOC-Generator, Hauptversion 128 x 64 Noppen (8 Baseplates 32x32).

Rekonstruktion nach Textquellen (siehe README: CONFIRMED-METLIFE / CONFIRMED-TOUR / INFERRED). Die Buehne ist eine
lange, gewundene Felsspalte (Fissure) quer durch den Innenraum: Laufweg in der Spalte, beidseitig zerkluefte
Felsmassen mit Terrassen und Ueberhaengen, Steinkoepfe (HEAD_A/B/C als verlinkte Submodelle), Hebeplattform,
Pyro-Zonen, Licht- und Lautsprechertuerme, LED-Waende, FOH, Freifallturm im Innenraum (MetLife).

Koordinaten (Blueprint): X = 0..127 (Laenge, von vorne gesehen links -> rechts), Y = 0..63 (Y = 0 hinten, 63 vorne).
LDraw: Zelle (i, k) = (63 - X, Y - 32); x = (i + 0.5) * 20, z = (k + 0.5) * 20, y nach unten (Boden y = 0).
Hoehen in Platten (P): 1 Stein = 3 P. Massstab ca. 1:50 (geschaetzt, siehe README): 1 Noppe = 0,40 m, 1 Platte = 0,16 m.

Aufruf: python3 generate_metlife_stage.py   -> .mpd, _bom.csv, _bricklink.xml, layout.json, Pruefbericht
"""
import json, math, os, random
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "circus_maximus_metlife"
random.seed(2024)

LDU, BH, PH = 20, 24, 8
RM = {0: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 90: [[0, 0, -1], [0, 1, 0], [1, 0, 0]],
      180: [[-1, 0, 0], [0, 1, 0], [0, 0, -1]], 270: [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]}
ROT_OUT = {(1, 0): 90, (-1, 0): 270, (0, 1): 180, (0, -1): 0}      # Gefaelle-Richtung -> Drehung (Standard -z)
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# ---------------- Farben (LDraw -> Name, BrickLink) ----------------
BLACK, DBG, LBG, DGRAY, PDGRAY, WHITE = 0, 72, 71, 8, 148, 15
TGREEN, TRED, TYELLOW, TNORANGE, TCLEAR, TBLACK, RED, YELLOW = 34, 36, 46, 57, 47, 40, 4, 14
COLORS = {0: ("Black", 11), 72: ("Dark Bluish Gray", 85), 71: ("Light Bluish Gray", 86), 8: ("Dark Gray", 10),
          148: ("Pearl Dark Gray", 77), 15: ("White", 1), 34: ("Trans-Green", 20), 36: ("Trans-Red", 17),
          46: ("Trans-Yellow", 19), 57: ("Trans-Neon Orange", 18), 47: ("Trans-Clear", 12),
          40: ("Trans-Black", 13), 4: ("Red", 5), 14: ("Yellow", 3)}

# ---------------- Teile (alle per LDraw-Bibliothek geprueft, siehe README "Teilestrategie") ----------------
BRICK = {(1, 1): "3005", (1, 2): "3004", (1, 3): "3622", (1, 4): "3010", (1, 6): "3009", (1, 8): "3008",
         (2, 2): "3003", (2, 3): "3002", (2, 4): "3001", (2, 6): "2456", (2, 8): "3007"}
BRICK_SMALL = {k: v for k, v in BRICK.items() if k[0] == 1 and k[1] <= 4}
PLATE = {(1, 1): "3024", (1, 2): "3023", (1, 3): "3623", (1, 4): "3710", (1, 6): "3666", (1, 8): "3460",
         (2, 2): "3022", (2, 3): "3021", (2, 4): "3020", (2, 6): "3795", (2, 8): "3034",
         (4, 4): "3031", (4, 6): "3032", (4, 8): "3035", (6, 6): "3958"}
PLATE_SMALL = {k: v for k, v in PLATE.items() if k[0] == 1 and k[1] <= 3}
TILE = {(1, 1): "3070b", (1, 2): "3069b", (1, 3): "63864", (1, 4): "2431", (2, 2): "3068b", (2, 4): "87079"}
TILE1 = {k: v for k, v in TILE.items() if k[0] == 1}
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "3062b": "3062", "6141": "4073", "2412b": "2412",
         "4032a": "4032", "3665a": "3665", "3811": "3811"}

SUBS = {"00_BASE": "Grundplatten, Innenraum", "01_MAIN_STAGE": "Spielflaechen (Weg-Belag, Plateaus, B-Stage)",
        "02_FISSURE": "Fissure: Laufweg-Unterbau in der Felsspalte", "03_ROCK_LEFT": "Fels links (X 0-43)",
        "04_ROCK_RIGHT": "Fels rechts (X 86-127)", "05_MAIN_ROCK": "Hauptfels Mitte (X 44-85)",
        "06_HEAD_A": "Kopf A (gross, bespielbar)", "07_HEAD_B": "Kopf B (Moai-Typ)", "08_HEAD_C": "Kopf C (klein, rund)",
        "09_LED_SYSTEM": "LED-Waende", "10_LIGHTING": "Licht: Moving Heads, Spots, Strobes, Laser",
        "11_SPEAKERS": "Lautsprecher: Line-Arrays, Subs", "12_PYRO": "Pyro-Zonen: Flammen, Duesen, Feuerwerk, Rauch",
        "13_LIFT": "Hebeplattform (Zustand 2: oben)", "14_TECHNICAL_RIG": "Traversen-Tuerme, FOH, Technikdeck",
        "15_FINAL_DETAILS": "Freifallturm, Absperrung, Faesser, Kabel"}
MASTERS = ["HEAD_MASTER_A", "HEAD_MASTER_B", "HEAD_MASTER_C", "13_LIFT_STATE1"]
MASTER_OF = {"06_HEAD_A": "HEAD_MASTER_A", "07_HEAD_B": "HEAD_MASTER_B", "08_HEAD_C": "HEAD_MASTER_C"}


def fmt(v):
    v = round(v, 3)
    return str(int(v)) if v == int(v) else str(v)


def mstr(M): return " ".join(fmt(round(v, 4)) for r in M for v in r)
def mv(M, v): return [sum(M[i][k] * v[k] for k in range(3)) for i in range(3)]


class Part:
    __slots__ = ("sub", "name", "color", "x", "y", "z", "M", "cells", "ytop", "ybot", "studs", "export")

    def __init__(s, sub, name, color, x, y, z, M, cells, ytop, ybot, studs=True, export=True):
        s.sub, s.name, s.color, s.x, s.y, s.z, s.M = sub, name, color, x, y, z, M
        s.cells, s.ytop, s.ybot = frozenset(cells), ytop, ybot
        s.studs = frozenset(cells) if studs is True else (frozenset(studs) if studs else frozenset())
        s.export = export

    def line(s):
        return f"1 {s.color} {fmt(s.x)} {fmt(s.y)} {fmt(s.z)} {mstr(s.M)} {s.name}.dat"


parts = []                       # Welt-Teile (fuer Checks; export=False bei Kopf-Instanzen)
local = defaultdict(list)        # Master-Submodelle (lokale Koordinaten)
refs = []                        # (sub, master, x, y, z, rot)


def rect(i0, k0, nx, nz): return [(i, k) for i in range(i0, i0 + nx) for k in range(k0, k0 + nz)]
def ik(X, Y): return (63 - X, Y - 32)
def XY(c): return (63 - c[0], c[1] + 32)


def place(sub, name, color, cells, ytop, h, studs=True, rot=None, y=None, into=None, export=True):
    xs = [c[0] for c in cells]; zs = [c[1] for c in cells]
    nx, nz = max(xs) - min(xs) + 1, max(zs) - min(zs) + 1
    if rot is None: rot = 90 if nz > nx else 0
    x = (min(xs) + max(xs) + 1) / 2 * LDU; z = (min(zs) + max(zs) + 1) / 2 * LDU
    p = Part(sub, name, color, x, ytop if y is None else y, z, RM[rot], cells, ytop, ytop + h, studs, export)
    (parts if into is None else into).append(p); return p


def deco(sub, name, color, x, y, z, rot=0, M=None, into=None):
    """Zubehoer ohne eigene Zellen (Klingen, Flammen am Stab ...), steckt in einem gezaehlten Teil"""
    p = Part(sub, name, color, x, y, z, M or RM[rot], [], 0, 0, False)
    (parts if into is None else into).append(p); return p


def pack(sub, cells, color, ytop, table, h, studs=True, prefer_x=True, colfn=None, into=None):
    todo = set(cells); out = []
    sizes = sorted(table, key=lambda s: -s[0] * s[1])
    for c in sorted(cells, key=lambda c: (c[1], c[0]) if prefer_x else (c[0], c[1])):
        if c not in todo: continue
        col = colfn(c) if colfn else color
        for a, b in sizes:
            done = False
            for nx, nz in (((b, a), (a, b)) if prefer_x else ((a, b), (b, a))):
                rc = rect(c[0], c[1], nx, nz)
                if all(q in todo and (not colfn or colfn(q) == col) for q in rc):
                    out.append(place(sub, table[(a, b)], col, rc, ytop, h, studs, into=into))
                    todo -= set(rc); done = True; break
            if done: break
    return out


def vnoise(x, z, sc=3.0, seed=0):
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx
    b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


def hrand(*a):
    return (math.sin(sum(v * (12.9898 + 7.1 * n) for n, v in enumerate(a)) + 78.233) * 43758.5453) % 1.0


def rock_col(c, level, top=False):
    """Vulkanisches Gestein: Dunkelgrau/Schwarz in Schichten, selten Dark Gray, Medium Stone Grey nur als Spur"""
    band = vnoise(level * 0.55, c[0] * 0.08 + c[1] * 0.05, 1.4, 5)
    n = vnoise(c[0] + level * 0.2, c[1], 5.0, 3)
    v = 0.4 * n + 0.6 * band + (hrand(c[0], c[1], level) - 0.5) * 0.08
    if top and v > 0.9: return LBG
    if v > 0.82: return DGRAY
    if v > 0.42: return DBG
    return BLACK


# =====================================================================================================
# 1. LAYOUT (Blueprint): Laufweg (Fissure), Felsbaender, Plateaus, Koepfe, Lift, Technik
# =====================================================================================================
X0, X1 = 0, 127
DECK = 9                                            # Weg-Hoehe in Platten (3 Steine, ca. 1,4 m)


def yc(X):                                          # Mittellinie des Laufwegs (gewunden, asymmetrisch)
    return 31.5 + 4.2 * math.sin(2 * math.pi * (X - 8) / 74) + 1.4 * math.sin(2 * math.pi * X / 23 + 1.1)


def hw(X):                                          # halbe Wegbreite
    w = 2.4 + 0.9 * vnoise(X, 0, 9, 21)
    if 82 <= X <= 91: w = max(w, 3.6)               # Lift-Bereich breiter
    return w


HF, KIND, MOD = {}, {}, {}                          # Hoehe (Platten), Art, Modul je Zelle
PATH = set()
for X in range(20, 108):
    for Y in range(64):
        if abs(Y + 0.5 - yc(X)) <= hw(X):
            c = ik(X, Y); PATH.add(c); HF[c] = DECK; KIND[c] = "weg"; MOD[c] = "02_FISSURE"

# Plateaus: links Kopf-A-Plaza, rechts B-Stage (rund) und Rear Stage (Technik)
HEADA_FOOT = {ik(X, Y) for X in range(6, 20) for Y in range(25, 37)}          # 14 x 12
PLAZA_A = {ik(X, Y) for X in range(4, 23) for Y in range(22, 41)
           if math.hypot((X - 13) / 10.5, (Y - 31) / 10) <= 1.0}
BSTAGE = {ik(X, Y) for X in range(104, 121) for Y in range(22, 42) if math.hypot(X + 0.5 - 112, Y + 0.5 - 32) <= 7.3}
REAR = {ik(X, Y) for X in range(119, 127) for Y in range(27, 37)}
for c in PLAZA_A: HF[c] = 12; KIND[c] = "plateau"; MOD[c] = "01_MAIN_STAGE"
for c in BSTAGE: HF[c] = 12; KIND[c] = "bstage"; MOD[c] = "01_MAIN_STAGE"
for c in REAR - BSTAGE: HF[c] = 9; KIND[c] = "rear"; MOD[c] = "14_TECHNICAL_RIG"
PATH -= PLAZA_A | BSTAGE | REAR
# Rampen/Stufen: Weg -> Plaza (links) und Weg -> B-Stage (rechts), 10 -> 11 Platten
for X in (20, 21):
    for Y in range(64):
        c = ik(X, Y)
        if c in PATH: HF[c] = 10 if X == 21 else 11
for X in (105, 106, 107):
    for Y in range(64):
        c = ik(X, Y)
        if c in PATH: HF[c] = {105: 10, 106: 11, 107: 11}[X]

# Felsbaender beidseits des Weges (zerklueftet, mit Luecken = Negativraeume / Zugaenge)
GAPS = {"n": [(33, 36), (90, 92)], "s": [(50, 53), (97, 99)]}
MAIN = (44, 85)


def band_t(X, side):
    if any(a <= X <= b for a, b in GAPS[side]): return 0
    t = 5.0 + 6.5 * vnoise(X, 1 if side == "n" else 7, 8, 31) + 2.5 * vnoise(X, 3, 3, 32)
    if MAIN[0] <= X <= MAIN[1]: t += 3.5 * math.sin(math.pi * (X - MAIN[0]) / (MAIN[1] - MAIN[0]))
    return t


def band_peak(X, side):
    p = 9 + 12 * vnoise(X, 11 if side == "n" else 17, 10, 41) + 4 * vnoise(X, 5, 4, 42)
    if MAIN[0] <= X <= MAIN[1]: p += 9 * math.sin(math.pi * (X - MAIN[0]) / (MAIN[1] - MAIN[0]))
    return p


for X in range(3, 125):
    ycx, hwx = yc(X), hw(X)
    for side, sg in (("n", -1), ("s", 1)):
        t = band_t(X, side)
        if t <= 0: continue
        pk = band_peak(X, side)
        for Y in range(64):
            d = (Y + 0.5 - ycx) * sg - hwx               # Abstand von der Wegkante (>0 = im Felsband)
            if d <= 0: continue
            jag = (vnoise(X * 1.3, Y * 1.3, 2.2, 51) - 0.5) * 3.2
            if d > t + jag: continue
            c = ik(X, Y)
            if c in HF: continue
            u = min(1.0, d / (t + 1.0))
            prof = math.sin(math.pi * min(1.0, 0.35 + 0.8 * u)) ** 0.6
            h = DECK + 3 + pk * prof
            if d > t - 1.5: h = min(h, DECK + 2 + 3 * vnoise(X, Y, 2, 61))   # Aussenkante faellt ab
            h = 3 * round(h / 3) + (1 if vnoise(X * 2, Y * 2, 1.5, 71) > 0.78 else 0)
            HF[c] = max(4, int(h)); KIND[c] = "fels"
            MOD[c] = "03_ROCK_LEFT" if X < 44 else "04_ROCK_RIGHT" if X > 85 else "05_MAIN_ROCK"

# Felsen um Plaza A und B-Stage (umschliessen die Enden)
for X in range(0, 128):
    for Y in range(64):
        c = ik(X, Y)
        if c in HF: continue
        for zone, cx, cy, rx, ry in ((PLAZA_A, 13, 31, 13.5, 13), (BSTAGE, 112, 32, 10.5, 11)):
            e = math.hypot((X + 0.5 - cx) / rx, (Y + 0.5 - cy) / ry) + (vnoise(X * 1.4, Y * 1.4, 2, 81) - 0.5) * 0.35
            if e <= 1.0:
                h = 12 + 15 * (1 - e) ** 0.5 * vnoise(X, Y, 5, 82) + 3
                HF[c] = max(4, 3 * round(h / 3)); KIND[c] = "fels"
                MOD[c] = "03_ROCK_LEFT" if X < 44 else "04_ROCK_RIGHT"
                break

# Kopf-Plateaus (flach) fuer die Koepfe B und C an den Flanken
HEADS = [  # (Master, Fussabdruck X0, Y0, Breite, Tiefe, Blickrichtung, Plateau-Hoehe)
    ("06_HEAD_A", 6, 25, 14, 12, 180, 12),
    ("07_HEAD_B", 62, 13, 10, 8, 0, 15),
    ("07_HEAD_B", 54, 43, 10, 8, 180, 15),
    ("08_HEAD_C", 93, 17, 8, 8, 0, 12),
    ("08_HEAD_C", 99, 41, 8, 8, 180, 12),
]
HEAD_CELLS = set()
for m, X0_, Y0_, Wd, Dp, rot, ph in HEADS:
    foot = {ik(X, Y) for X in range(X0_, X0_ + Wd) for Y in range(Y0_, Y0_ + Dp)}
    pad = {ik(X, Y) for X in range(X0_ - 1, X0_ + Wd + 1) for Y in range(Y0_ - 1, Y0_ + Dp + 1)}
    for c in pad:
        if c in PATH: continue
        HF[c] = ph
        if KIND.get(c) not in ("plateau",): KIND[c] = "kopfsockel"
        MOD.setdefault(c, "05_MAIN_ROCK")
        if XY(c)[0] < 44: MOD[c] = "03_ROCK_LEFT"
        elif XY(c)[0] > 85: MOD[c] = "04_ROCK_RIGHT"
        else: MOD[c] = "05_MAIN_ROCK"
    assert not foot & PATH, ("Kopf im Weg", m, X0_)
    HEAD_CELLS |= foot

# Lift im Weg
LIFT = {ik(X, Y) for X in range(84, 90) for Y in range(int(round(yc(86.5) - 3)), int(round(yc(86.5) - 3)) + 6)}
for c in LIFT: HF[c] = DECK; KIND[c] = "lift"; MOD[c] = "02_FISSURE"; PATH.add(c)

# Rock-Kronen: lokale Hochpunkte (fuer Pyro/Laser)
ROCK = {c for c, k in KIND.items() if k == "fels"}
CREST = sorted([c for c in ROCK if all(HF.get((c[0] + a, c[1] + b), 0) <= HF[c] for a in (-1, 0, 1) for b in (-1, 0, 1))
                and HF[c] >= 18], key=lambda c: -HF[c])

# =====================================================================================================
# 2. GRUNDPLATTEN
# =====================================================================================================
for m in range(4):
    for kz in (-1, 0):
        i0 = -64 + 32 * m; k0 = -32 + 32 * (kz + 1)
        parts.append(Part("00_BASE", "3811", BLACK, (i0 + 16) * LDU, 0, (k0 + 16) * LDU, RM[0],
                          rect(i0, k0, 32, 32), 0, 4))

# =====================================================================================================
# 3. UNTERBAU (Foundation): Steinlagen mit Verband, Aussenhaut in kleinen Teilen, Kern gross und schwarz
# =====================================================================================================
SOLID = {c for c, h in HF.items() if h > 0}
GMAX = max(HF.values()) // 3 + 1
texture = []
for g in range(GMAX):
    S = {c for c in SOLID if HF[c] >= 3 * (g + 1)}
    if not S: continue
    yt = -(g + 1) * BH
    ext = {c for c in S if any((c[0] + a, c[1] + b) not in S for a, b in DIRS)}
    for mod in set(MOD[c] for c in S):
        core = {c for c in S - ext if MOD[c] == mod}
        skin = {c for c in ext if MOD[c] == mod}
        pack(mod, core, BLACK, yt, BRICK, BH, prefer_x=g % 2 == 0)
        out = pack(mod, skin, None, yt, BRICK_SMALL, BH, prefer_x=g % 2 == 1,
                   colfn=lambda c, g=g: BLACK if KIND[c] in ("weg", "lift", "rear") else rock_col(c, 3 * g))
        texture += [p for p in out if KIND[next(iter(p.cells))] in ("fels", "kopfsockel")]
# Platten-Reste (HF nicht durch 3 teilbar)
for lvl in range(1, max(HF.values()) + 1):
    S = {c for c in SOLID if HF[c] >= lvl and lvl > 3 * (HF[c] // 3)}
    if not S: continue
    for mod in set(MOD[c] for c in S):
        pack(mod, {c for c in S if MOD[c] == mod}, None, -lvl * PH, PLATE, PH, prefer_x=lvl % 2 == 0,
             colfn=lambda c, lvl=lvl: BLACK if KIND[c] in ("weg", "lift", "rear") else rock_col(c, lvl))
# Oberflaechen-Textur der Felswaende: Rundsteine und Rillensteine (Log) statt glatter Steine
for p in texture:
    r = hrand(p.x, p.z, p.ytop)
    if p.name == "3005" and r < 0.22: p.name = "3062b"
    elif p.name == "3004" and r < 0.25: p.name = "30136"

# =====================================================================================================
# 4. MIKRO-DETAIL: Felskappen, Ueberhaenge, Wegbelag, Plateaus
# =====================================================================================================
USED_TOP = set(HEAD_CELLS)           # Zellen, deren Oberseite schon belegt ist (Koepfe, Technik, Pyro ...)
RESERVE = {}                         # Zelle -> Zweck (vor den Kappen reservieren)


def reserve(c, why): RESERVE[c] = why; USED_TOP.add(c)


# Pyro- und Laser-Positionen auf Felskronen reservieren (Zonen siehe README)
PYRO_RIDGE = []
for c in CREST:
    if len(PYRO_RIDGE) >= 12: break
    if c in USED_TOP or any(math.hypot(c[0] - q[0], c[1] - q[1]) < 7 for q in PYRO_RIDGE): continue
    PYRO_RIDGE.append(c); reserve(c, "pyro_ridge")
LASERS = []
for c in CREST:
    if len(LASERS) >= 8: break
    if c in USED_TOP or any(math.hypot(c[0] - q[0], c[1] - q[1]) < 9 for q in LASERS + PYRO_RIDGE): continue
    LASERS.append(c); reserve(c, "laser")
# Fissure-Pyro: Felszellen direkt an der Wegkante
PYRO_FISS = []
for X in (28, 47, 66, 78, 96, 101):
    Yc = yc(X); hwx = hw(X)
    for Y in ([int(Yc - hwx - 1)] if X % 2 else [int(Yc + hwx + 1)]):
        c = ik(X, Y)
        if c in ROCK and c not in USED_TOP: PYRO_FISS.append(c); reserve(c, "pyro_fiss")
# Bodenstrahler an der Wegkante (klein und zahlreich)
EDGE_LIGHTS = []
for X in range(24, 104, 5):
    for Y in (int(yc(X) - hw(X) - 1), int(yc(X) + hw(X) + 1)):
        c = ik(X, Y)
        if c in ROCK and c not in USED_TOP: EDGE_LIGHTS.append(c); reserve(c, "licht")
DRUMS = [c for c in (ik(8, 23), ik(17, 39), ik(110, 26), ik(115, 38)) if HF.get(c) == 12 and c not in HEAD_CELLS]
for c in DRUMS: reserve(c, "fass")
# Plaza-A Flammen (Zone 1)
PYRO_A = [ik(5, 23), ik(21, 23), ik(5, 39), ik(21, 39)]
for c in PYRO_A: reserve(c, "pyro_a")

# Ueberhaenge: Felskante ueber dem Innenraum, Platte 1x2 ragt eine Noppe hinaus
LIPS = []
for c in sorted(ROCK):
    if c in USED_TOP or HF[c] < 15: continue
    for d in DIRS:
        o = (c[0] + d[0], c[1] + d[1])
        if HF.get(o, 0) == 0 and o not in USED_TOP and hrand(c[0], c[1], 9) < 0.35 \
                and -64 <= o[0] < 64 and -32 <= o[1] < 32:
            LIPS.append((c, o, d)); USED_TOP.add(c); USED_TOP.add(o); break
for c, o, d in LIPS:
    y = -HF[c] * PH
    place(MOD[c], "3023", rock_col(c, HF[c]), [c, o], y - PH, PH)
    place(MOD[c], "54200", rock_col(o, HF[c], True), [o], y - PH - 16, 16, studs=False, rot=ROT_OUT[d], y=y - PH)
    place(MOD[c], "3070b", rock_col(c, HF[c] + 1, True), [c], y - 2 * PH, PH, studs=False)

# Felskappen: Cheese-Slopes an Kanten (Gefaelle nach aussen), Vierfach-Slopes auf Spitzen, Fliesen,
# Rundfliesen, offene Noppen (Rauhigkeit) auf Flaechen
caps_tile = defaultdict(dict)
for c in sorted(ROCK | {c for c, k in KIND.items() if k == "kopfsockel"}):
    if c in USED_TOP: continue
    h = HF[c]; y = -h * PH
    lower = [d for d in DIRS if HF.get((c[0] + d[0], c[1] + d[1]), 0) < h]
    zone = vnoise(c[0], c[1], 6.0, 19)                    # Flaechen-Charakter
    r = hrand(c[0], c[1], 3) * 0.35 + zone * 0.65
    if KIND[c] == "kopfsockel":
        caps_tile[(h, MOD[c])][c] = DBG if r < 0.7 else BLACK; continue
    rr = hrand(c[0], c[1], 3)
    if len(lower) >= 3:                                          # Spitze: Vierfach-Slope
        place(MOD[c], "22388", rock_col(c, h, True), [c], y - 16, 16, studs=False, y=y)
    elif lower and zone < 0.78:                                  # Kante: Cheese-Slope folgt dem Gefaelle
        place(MOD[c], "54200", rock_col(c, h, True), [c], y - 16, 16, studs=False, rot=ROT_OUT[lower[0]], y=y)
    elif zone < 0.36:                                            # Ruhezone: glatte Felsplatte
        caps_tile[(h, MOD[c])][c] = rock_col(c, h, True)
    elif zone < 0.56:                                            # rauhe Zone: offene Noppen, wenige Rundfliesen
        if rr < 0.25: place(MOD[c], "98138", rock_col(c, h, True), [c], y - PH, PH, studs=False)
    elif zone < 0.72:                                            # porige Zone: Rundfliesen / Rundplatten
        place(MOD[c], "98138" if rr < 0.6 else "6141", rock_col(c, h, True), [c], y - PH, PH,
              studs=rr >= 0.6)
    else:                                                        # Geroell: Rundplatten, Fliesen, kleine Slopes
        if rr < 0.4: place(MOD[c], "6141", rock_col(c, h, True), [c], y - PH, PH)
        elif rr < 0.7: place(MOD[c], "3024", rock_col(c, h, True), [c], y - PH, PH)
        else: place(MOD[c], "54200", rock_col(c, h, True), [c], y - 16, 16, studs=False,
                    rot=ROT_OUT[DIRS[int(rr * 40) % 4]], y=y)
for (h, mod), cc in caps_tile.items():
    pack(mod, cc, None, -h * PH - PH, TILE, PH, studs=False, colfn=lambda c, cc=cc: cc[c])

# Laufweg: Belag aus Fliesen (schwarz/dunkelgrau, Gitter = Bodenluken), Plaza/B-Stage glatt
walk = {c for c in PATH if c not in LIFT}
for h in set(HF[c] for c in walk):
    cells = {c for c in walk if HF[c] == h}
    pack("01_MAIN_STAGE", cells, None, -h * PH - PH, TILE, PH, studs=False, prefer_x=False,
         colfn=lambda c: DBG if vnoise(c[0], c[1], 3, 91) > 0.62 else BLACK)
for zone, colA, colB in ((PLAZA_A - HEAD_CELLS, DBG, BLACK), (BSTAGE, BLACK, DBG)):
    cells = {c for c in zone if c not in USED_TOP and c not in RESERVE}
    pack("01_MAIN_STAGE", cells, None, -12 * PH - PH, TILE, PH, studs=False,
         colfn=lambda c, a=colA, b=colB: a if (c[0] + c[1]) % 7 else b)
rear_cells = {c for c in REAR - BSTAGE}
pack("14_TECHNICAL_RIG", rear_cells, None, -9 * PH - PH, {(1, 2): "2412b", (1, 1): "3070b"}, PH, studs=False,
     colfn=lambda c: DBG)

# =====================================================================================================
# 5. KOEPFE: Master-Submodelle (Voxel-Skulptur aus Platten), verlinkt platziert
# =====================================================================================================
HEAD_SPECS = {
    # Breite, Tiefe, Hoehe (Platten), Variante
    "HEAD_MASTER_A": (14, 12, 48, "A"),
    "HEAD_MASTER_B": (10, 8, 40, "B"),
    "HEAD_MASTER_C": (8, 8, 28, "C"),
}


def head_voxels(W, D, Hp, var):
    """Voxel (a, b, l): a = -W/2..W/2-1 (quer), b = -D/2..D/2-1 (Gesicht bei b = -D/2, Blick -z), l = Lage."""
    V = set(); socket = set(); crack = set()
    seed = {"A": 1, "B": 2, "C": 3}[var]
    for l in range(Hp):
        t = (l + 0.5) / Hp
        if var == "B":              # Moai: lang, flacher Schaedel, schmale Wangen
            hx = 0.55 if t < 0.1 else 0.78 if t < 0.25 else 0.86 if t < 0.82 else 0.86 * math.sqrt(max(0, 1 - ((t - 0.82) / 0.2) ** 2))
            hz = 0.7 if t < 0.1 else 0.95 if t < 0.85 else 0.95 * math.sqrt(max(0, 1 - ((t - 0.85) / 0.17) ** 2))
        else:
            hx = 0.6 if t < 0.12 else 0.72 + 0.6 * (t - 0.12) if t < 0.32 else 0.9 if t < 0.7 else \
                0.9 * math.sqrt(max(0, 1 - ((t - 0.7) / 0.31) ** 2))
            hz = 0.72 if t < 0.12 else 0.92 if t < 0.7 else 0.92 * math.sqrt(max(0, 1 - ((t - 0.7) / 0.32) ** 2))
            if var == "A" and t > 0.9: hx, hz = 0, 0               # A: Schaedel oben abgebrochen (Spielflaeche)
        for a in range(-W // 2, W // 2):
            for b in range(-D // 2, D // 2):
                u = (a + 0.5) / (W / 2); w = (b + 0.5) / (D / 2)
                if hx <= 0: continue
                rough = (vnoise(a * 1.7 + l * 0.2, b * 1.7, 1.8, seed * 13) - 0.5) * 0.18
                p = 2.6
                if abs(u / (hx + rough)) ** p + abs((w - 0.04) / (hz + rough)) ** p <= 1.0:
                    V.add((a, b, l))
        if var == "A" and 0.84 < t <= 0.9:                        # Bruchkante: Ecke fehlt
            V -= {(a, b, l) for a in range(W // 2 - 4, W // 2) for b in range(-D // 2, -D // 2 + 4)}

    def front(a, l):
        bs = [b for (aa, b, ll) in V if aa == a and ll == l]
        return min(bs) if bs else None
    nose_w = {"A": (-1, 0), "B": (-1, 0), "C": (-1, 0)}[var]
    for l in range(Hp):
        t = (l + 0.5) / Hp
        # Nase (Moai: lang und gerade), Kinn, Brauenwulst, Lippen
        if (0.36 if var != "B" else 0.33) <= t <= (0.6 if var != "B" else 0.66):
            for a in nose_w:
                f = front(a, l)
                if f is not None:
                    lo = 0.36 if var != "B" else 0.33
                    prot = 3 if var == "B" and t < 0.45 else 2 if t < lo + 0.12 or var == "B" else 1
                    for k in range(1, prot + 1): V.add((a, f - k, l))
                    if t < lo + 0.05:                                   # Nasenfluegel
                        for aa in (min(nose_w) - 1, max(nose_w) + 1):
                            ff = front(aa, l)
                            if ff is not None: V.add((aa, ff - 1, l))
        if 0.13 <= t <= 0.2:
            for a in range(-W // 4, W // 4):
                f = front(a, l)
                if f is not None: V.add((a, f - 1, l))
        if var in ("A", "B") and (0.21 <= t <= 0.235 or 0.275 <= t <= 0.3):
            for a in range(-int(W * 0.2), int(W * 0.2)):
                f = front(a, l)
                if f is not None: V.add((a, f - 1, l))
        if 0.58 <= t <= 0.64 and var != "C":
            for a in range(-int(W * 0.38), int(W * 0.38)):
                f = front(a, l)
                if f is not None: V.add((a, f - 1, l))
    for l in range(Hp):
        t = (l + 0.5) / Hp
        # Augenhoehlen (Laser-Augen), Mund, Ohren
        if 0.47 <= t <= 0.56:
            for cxa in (-int(W * 0.24) - 1, int(W * 0.24)):
                for a in (cxa, cxa + (1 if W >= 10 else 0)):
                    f = front(a, l)
                    if f is not None:
                        for k in range(2 if W >= 10 else 1):
                            V.discard((a, f + k, l)); socket.add((a, f + k, l))
        if 0.24 <= t <= 0.27:
            for a in range(-int(W * 0.2), int(W * 0.2)):
                f = front(a, l)
                if f is not None:
                    for k in range(2 if abs(a) < W * 0.12 else 1):
                        V.discard((a, f + k, l)); crack.add((a, f + k, l))
        if 0.42 <= t <= 0.6 and not (var == "C" and t > 0.5):
            for sgn in (-1, 1):
                aa = [a for (a, b, ll) in V if ll == l and b in (0, 1)]
                if aa:
                    edge = max(aa) if sgn > 0 else min(aa)
                    if -W // 2 - 1 <= edge + sgn < W // 2 + 1: V.add((edge + sgn, 0, l))
    # Risse: zufaellige senkrechte Linien auf der Oberflaeche, 1 Voxel tief
    rnd = random.Random(seed * 7)
    for _ in range({"A": 4, "B": 3, "C": 3}[var]):
        a = rnd.randint(-W // 2 + 1, W // 2 - 2); l = rnd.randint(int(Hp * 0.25), int(Hp * 0.85))
        for step in range(rnd.randint(6, 12)):
            f = front(a, l)
            if f is not None and (a, f, l) not in socket:
                V.discard((a, f, l)); crack.add((a, f, l))
            l -= 1; a += rnd.choice((-1, 0, 0, 1))
            if l < 2: break
    return V, socket, crack


def build_head(master, W, D, Hp, var):
    V, socket, crack = head_voxels(W, D, Hp, var)
    out = local[master]
    lay = defaultdict(set)
    for a, b, l in V: lay[l].add((a, b))
    stone = {"A": (DBG, LBG), "B": (DBG, DGRAY), "C": (DBG, LBG)}[var]

    hollow = socket | crack

    def scol(c, l):
        """Stein mit Licht von oben (hell oben, dunkel unten), schwarze Wandungen in Hoehlen/Rissen/Mund"""
        if (c[0], c[1], l) in crack: return BLACK
        if any((c[0] + a, c[1] + b, l) in hollow for a, b in DIRS) or (c[0], c[1], l + 1) in hollow:
            return BLACK
        n = vnoise(c[0] * 1.3 + l * 0.15, c[1] * 1.3, 2.0, 7 + ord(var)) + 0.25 * (l / Hp - 0.5)
        return stone[1] if n > 0.78 else stone[0] if n > 0.18 else BLACK
    for l in range(Hp):
        L = lay[l]
        if not L: continue
        y = -(l + 1) * PH
        surf = {c for c in L if any((c[0] + a, c[1] + b) not in L for a, b in DIRS)
                or c not in lay[l + 1] or c not in lay[l - 1]}
        core = L - surf
        below = lay[l - 1] if l > 0 else L
        used = set()
        # Ueberhaenge zuerst: ungestuetzte Zelle + gestuetzter Nachbar als 1x2-Platte
        for c in sorted(L - below, key=lambda c: -(abs(c[0]) + abs(c[1]))):
            if c in used: continue
            done = False
            for ln in (2, 3, 4):                                  # 1x2 .. 1x4 bis in die gestuetzte Zone
                for d in sorted(DIRS, key=lambda d: (c[0] + d[0]) ** 2 + (c[1] + d[1]) ** 2):
                    run = [(c[0] + d[0] * j, c[1] + d[1] * j) for j in range(ln)]
                    if all(q in L and q not in used for q in run) and run[-1] in below:
                        place(master, PLATE[(1, ln)], scol(c, l), run, y, PH, into=out)
                        used |= set(run); done = True; break
                if done: break
        pack(master, core - used, BLACK, y, PLATE, PH, prefer_x=l % 2 == 0, into=out)
        pack(master, surf - used, None, y, PLATE_SMALL, PH, prefer_x=l % 2 == 1, into=out,
             colfn=lambda c, l=l: scol(c, l))
        # Kappen auf offenen Oberseiten
        above = lay[l + 1]; above2 = lay[l + 2]
        for c in sorted(L - above):
            if (c[0], c[1], l + 1) in socket or (c[0], c[1], l + 1) in crack:
                place(master, "98138", TRED if (c[0], c[1], l + 1) in socket else BLACK, [c], y - PH, PH,
                      studs=False, into=out); continue
            outward = [d for d in DIRS if (c[0] + d[0], c[1] + d[1]) not in L]
            free2 = c not in above2
            if outward and free2:
                d = (0, -1) if (0, -1) in outward else outward[0]
                place(master, "54200", scol(c, l + 1), [c], y - 16, 16, studs=False, rot=ROT_OUT[d], y=y,
                      into=out)
            else:
                place(master, "3070b", scol(c, l + 1), [c], y - PH, PH, studs=False, into=out)
    return V


def prune(master):
    """Teile ohne Verbindung zur Standflaeche entfernen (Voxel-Inseln = abgebrochener Stein)"""
    ps = local[master]
    idx = defaultdict(list)
    for n, p in enumerate(ps):
        for c in p.studs: idx[(p.ytop, c)].append(n)
    adj = defaultdict(set)
    for n, p in enumerate(ps):
        for c in p.cells:
            for m in idx.get((p.ybot, c), []): adj[n].add(m); adj[m].add(n)
    seen = {n for n, p in enumerate(ps) if p.ybot == 0}; st = list(seen)
    while st:
        n = st.pop()
        for m in adj[n]:
            if m not in seen: seen.add(m); st.append(m)
    keep = [p for n, p in enumerate(ps) if n in seen or not p.cells]
    removed = len(ps) - len(keep); local[master] = keep
    return removed


HEAD_V, PRUNED = {}, {}
for m, (W, D, Hp, var) in HEAD_SPECS.items():
    HEAD_V[m] = build_head(m, W, D, Hp, var)
    PRUNED[m] = prune(m)
print("Kopf-Inseln entfernt:", PRUNED)


def instantiate(master, sub, ti, tk, y0, rot):
    """Master als verlinktes Submodell: Weltkopien nur fuer die Pruefung, Export als Referenz"""
    M = RM[rot]
    for p in local[master]:
        cells = set()
        for (a, b) in p.cells:
            cx, _, cz = mv(M, [a + 0.5, 0, b + 0.5]); cells.add((math.floor(cx + ti), math.floor(cz + tk)))
        stc = set()
        for (a, b) in p.studs:
            cx, _, cz = mv(M, [a + 0.5, 0, b + 0.5]); stc.add((math.floor(cx + ti), math.floor(cz + tk)))
        parts.append(Part(sub, p.name, p.color, 0, 0, 0, RM[0], cells, p.ytop + y0, p.ybot + y0, stc or False,
                          export=False))
    refs.append((sub, master, ti * LDU, y0, tk * LDU, rot))


for m, X0_, Y0_, Wd, Dp, rot, ph in HEADS:
    W, D, Hp, var = HEAD_SPECS[MASTER_OF[m]]
    # Fussabdruck-Mitte als Gitterpunkt (Welt): Zellen X0..X0+W-1 -> i von 63-X0-W+1 .. 63-X0
    ti = (63 - X0_ - Wd + 1 + 63 - X0_ + 1) / 2
    tk = (Y0_ - 32 + Y0_ - 32 + Dp) / 2
    sw, sd = (Wd, Dp)
    assert (W, D) == ((sw, sd) if rot in (0, 180) else (sd, sw)), m
    instantiate(MASTER_OF[m], m, ti, tk, -ph * PH, rot)

# =====================================================================================================
# 6. HEBEPLATTFORM (13_LIFT): Zustand 2 oben im Modell, Zustand 1 als eigenes Submodell
# =====================================================================================================
LI = sorted(LIFT)
li0 = min(c[0] for c in LI); lk0 = min(c[1] for c in LI)
LUP = 30                                             # Hub in Platten (10 Steine, ca. 4,8 m)


def build_lift(sub, rise, into=None):
    y = -DECK * PH
    base = rect(li0, lk0, 6, 6)
    pack(sub, base, BLACK, y - PH, PLATE, PH, into=into)                          # Grundrahmen
    y -= PH
    if rise > 0:
        # Scherenstruktur: zwei Seitenwaende aus versetzten 1x2-Platten (Zickzack = gekreuzte Scheren)
        n = rise - 2
        for l in range(n):
            ph_ = (l * 5) // n                                                     # 0..4 Position
            for side in (lk0, lk0 + 5):
                a = li0 + ph_; b = li0 + 4 - ph_
                cells = {(a, side), (a + 1, side)} | {(b, side), (b + 1, side)}
                cells = {c for c in cells if li0 <= c[0] < li0 + 6}
                pack(sub, cells, DBG if l % 2 else BLACK, y - (l + 1) * PH, PLATE_SMALL, PH, into=into)
            # Fuehrung: Mittelsaeule (Hydraulik) aus runden Platten
            for c in ((li0 + 2, lk0 + 2), (li0 + 3, lk0 + 3)):
                place(sub, "6141", LBG if l % 3 == 0 else DBG, [c], y - (l + 1) * PH, PH, into=into)
        y -= n * PH
        # Unterseite: Traegerrost
        pack(sub, rect(li0, lk0, 6, 6), BLACK, y - PH, PLATE, PH, into=into); y -= PH
    pack(sub, rect(li0, lk0, 6, 6), BLACK, y - PH, PLATE, PH, prefer_x=False, into=into); y -= PH   # Buehnenplatte
    cells = rect(li0, lk0, 6, 6)
    pack(sub, cells, None, y - PH, TILE, PH, studs=False, into=into,
         colfn=lambda c: DBG if c[0] in (li0, li0 + 5) or c[1] in (lk0, lk0 + 5) else BLACK)
    return y


build_lift("13_LIFT", LUP)
lift1 = []
build_lift("13_LIFT_STATE1", 0, into=lift1)
local["13_LIFT_STATE1"] = lift1

# =====================================================================================================
# 7. TECHNIK: Traversen-Tuerme (Licht/Lautsprecher/LED), FOH
# =====================================================================================================
FLOOR_USED = set(SOLID) | {o for c, o, d in LIPS}


def floor_free(cells): return all(c not in FLOOR_USED for c in cells)


def moving_head(sub, c, y, into=None):
    """kleiner Moving Head: Buegel (Rundplatte) + Kopf (Rundstein) + Linse (Rundfliese trans-klar)"""
    place(sub, "6141", BLACK, [c], y - PH, PH, into=into)
    place(sub, "3062b", BLACK, [c], y - PH - BH, BH, into=into)
    place(sub, "98138", TCLEAR, [c], y - PH - BH - PH, PH, studs=False, into=into)


def truss(sub, i0, k0, h_bricks, into):
    """2x2-Traverse aus Technic-Steinen (Lochreihen = Fachwerk-Optik), Lagen kreuzweise, auf Fussplatte"""
    place(sub, "3022", DBG, rect(i0, k0, 2, 2), -PH, PH, into=into)
    for g in range(h_bricks):
        yt = -PH - (g + 1) * BH
        if g % 2 == 0:
            for kk in (k0, k0 + 1): place(sub, "3700", BLACK, rect(i0, kk, 2, 1), yt, BH, into=into)
        else:
            for ii in (i0, i0 + 1): place(sub, "3700", BLACK, rect(ii, k0, 1, 2), yt, BH, rot=90, into=into)
    return -PH - h_bricks * BH


def instance(master, sub, cells_world, ti, tk, rot, y0=0):
    FLOOR_USED.update(cells_world)
    instantiate(master, sub, ti, tk, y0, rot)


# ---- Master: Lichtturm (2x2-Traverse, Kopftraeger 6x2, oben Moving Heads + Spots, unten haengend) ----
MASTERS += ["LIGHT_TOWER", "SPEAKER_TOWER", "LED_PANEL"]
LT = local["LIGHT_TOWER"]
yt_ = truss("10_LIGHTING", -1, -1, 14, LT)
place("10_LIGHTING", "3795", BLACK, rect(-3, -1, 6, 2), yt_ - PH, PH, into=LT)
for c in rect(-3, -1, 6, 2):
    if -1 <= c[0] <= 0:
        place("10_LIGHTING", "3070b", BLACK, [c], yt_ - 2 * PH, PH, studs=False, into=LT); continue
    if c[1] == -1: moving_head("10_LIGHTING", c, yt_ - PH, into=LT)
    else: place("10_LIGHTING", "6141", TCLEAR, [c], yt_ - 2 * PH, PH, into=LT)
    place("10_LIGHTING", "6141", BLACK, [c], yt_, PH, into=LT)                            # haengend: Buegel
    place("10_LIGHTING", "3062b", BLACK if c[1] == -1 else WHITE, [c], yt_ + PH, BH, into=LT)   # Kopf / Strobe
LIGHT_TOWERS = [(46, 2), (80, 2), (46, 60), (80, 60)]
for X, Y in LIGHT_TOWERS:
    i_, k_ = ik(X + 1, Y)                                   # Zellen X..X+1, Y..Y+1 -> Ecke i_, k_
    instance("LIGHT_TOWER", "14_TECHNICAL_RIG", rect(i_ - 2, k_, 6, 2), i_ + 1, k_ + 1, 0)

# ---- Master: Lautsprecherturm (Traverse, Kragarm, haengendes Line-Array aus 8 Gitter-Steinen, Subs) ----
ST = local["SPEAKER_TOWER"]
yt_ = truss("11_SPEAKERS", -1, -1, 13, ST)
place("11_SPEAKERS", "3020", BLACK, rect(-1, -1, 2, 4), yt_ - PH, PH, into=ST)            # Kragarm nach +z
yb = yt_
for n_ in range(8):
    place("11_SPEAKERS", "2877", BLACK, [(-1, 2), (0, 2)], yb, BH, rot=180, into=ST); yb += BH
for g in range(2): place("11_SPEAKERS", "3003", BLACK, rect(-4, -1, 2, 2), -(g + 1) * BH, BH, into=ST)
pack("11_SPEAKERS", rect(-4, -1, 2, 2), BLACK, -2 * BH - PH, {(1, 2): "2412b"}, PH, studs=False, into=ST)
SPEAKERS = [(28, 2, 1), (98, 2, 1), (28, 60, -1), (98, 60, -1)]    # (X, Y, Richtung zur Buehne in Y)
for X, Y, face in SPEAKERS:
    i_, k_ = ik(X + 1, Y)
    rot = 0 if face > 0 else 180
    cw = (rect(i_ - 3, k_, 5, 2) + rect(i_, k_ + 2, 2, 2)) if face > 0 else (rect(i_, k_, 5, 2) + rect(i_, k_ - 2, 2, 2))
    instance("SPEAKER_TOWER", "11_SPEAKERS", cw, i_ + 1, k_ + 1, rot)

# ---- Master: LED-Panel (Modulraster 2 x 1 Stein, Rahmen dunkelgrau, Traverse hinten, Licht oben) ----
LED_W, LED_H, LED_RISE = 14, 11, 2
LP = local["LED_PANEL"]
row = [(a, -1) for a in range(-7, 7)]; back = [(a, 0) for a in range(-7, 7)]
pack("09_LED_SYSTEM", row + back, BLACK, -PH, PLATE, PH, into=LP)
for g in range(LED_RISE):
    for a0 in (-7, -1, 5):
        place("09_LED_SYSTEM", "3003", BLACK, rect(a0, -1, 2, 2), -PH - (g + 1) * BH, BH, into=LP)
y0 = -PH - LED_RISE * BH
pack("09_LED_SYSTEM", row + back, BLACK, y0 - PH, PLATE, PH, into=LP); y0 -= PH
for g in range(LED_H):
    yt = y0 - (g + 1) * BH
    for a in range(-6, 6, 2): place("09_LED_SYSTEM", "3004", BLACK, [(a, -1), (a + 1, -1)], yt, BH, into=LP)
    for a in (-7, 6): place("09_LED_SYSTEM", "3005", DBG, [(a, -1)], yt, BH, into=LP)
    for a in (-7, -3, 1, 5): place("09_LED_SYSTEM", "6541", BLACK, [(a, 0)], yt, BH, into=LP)
yt = y0 - LED_H * BH
pack("09_LED_SYSTEM", row + back, BLACK, yt - PH, PLATE, PH, into=LP)
pack("09_LED_SYSTEM", row, DBG, yt - 2 * PH, TILE1, PH, studs=False, into=LP)
for a in range(-6, 7, 3): moving_head("10_LIGHTING", (a, 0), yt - PH, into=LP)
# vier Screens an den Stirnseiten, Blick nach aussen zu den Zuschauern hinter den Buehnenenden
LEDS = [(0, 2, 90), (0, 48, 90), (126, 2, 270), (126, 48, 270)]   # (X0, Y0, Drehung)
for X0_, Y0_, rot in LEDS:
    cw = [ik(X, Y) for X in (X0_, X0_ + 1) for Y in range(Y0_, Y0_ + LED_W)]
    i_ = min(c[0] for c in cw); k_ = min(c[1] for c in cw)
    instance("LED_PANEL", "09_LED_SYSTEM", cw, i_ + 1, k_ + 7, rot)

# FOH (Front of House) im Innenraum vorne: Podest, Mischpult (Gitterfliesen), Dach auf vier Stuetzen
FOH = [ik(X, Y) for X in range(58, 66) for Y in range(53, 58)]
FLOOR_USED.update(FOH)
pack("14_TECHNICAL_RIG", FOH, BLACK, -BH, BRICK, BH)
fi0 = min(c[0] for c in FOH); fk0 = min(c[1] for c in FOH)
DESK = set(rect(fi0 + 2, fk0 + 2, 4, 2))
POSTS = [(fi0, fk0), (fi0 + 7, fk0), (fi0, fk0 + 4), (fi0 + 7, fk0 + 4)]
pack("14_TECHNICAL_RIG", [c for c in FOH if c not in DESK and c not in POSTS], DBG, -BH - PH, TILE, PH, studs=False)
place("14_TECHNICAL_RIG", "3020", DBG, sorted(DESK), -BH - PH, PH)
pack("14_TECHNICAL_RIG", sorted(DESK), BLACK, -BH - 2 * PH, {(1, 2): "2412b"}, PH, studs=False)
for c in POSTS:
    for g in range(4): place("14_TECHNICAL_RIG", "3062b", BLACK, [c], -BH - (g + 1) * BH, BH)
pack("14_TECHNICAL_RIG", FOH, BLACK, -5 * BH - PH, PLATE, PH)                     # Dach
pack("14_TECHNICAL_RIG", FOH, BLACK, -5 * BH - 2 * PH, TILE, PH, studs=False)

# =====================================================================================================
# 8. PYRO (12_PYRO): Zonen
# =====================================================================================================
def flame(sub, c, y, big=False):
    """Flammensaeule auf Duese: gelb unten, neon-orange oben, Spitze als Kegel"""
    place(sub, "3062b", BLACK, [c], y - BH, BH)                     # Duese
    yy = y - BH
    for col in ([TYELLOW, TNORANGE, TNORANGE] if big else [TYELLOW, TNORANGE]):
        place(sub, "3062b", col, [c], yy - BH, BH); yy -= BH
    place(sub, "4589", TNORANGE, [c], yy - BH, BH, studs=False)


def nozzle(sub, c, y):
    place(sub, "6141", BLACK, [c], y - PH, PH)
    place(sub, "6141", DBG, [c], y - 2 * PH, PH)


# Zone 1: Kopf A / Plaza – vier grosse Flammenwerfer
for c in PYRO_A:
    if c in HF: flame("12_PYRO", c, -HF[c] * PH, big=True)
# Zone 2: Felskronen – Duesenreihe, jede dritte feuert
for n_, c in enumerate(PYRO_RIDGE):
    if n_ % 3 == 0: flame("12_PYRO", c, -HF[c] * PH)
    else: nozzle("12_PYRO", c, -HF[c] * PH)
# Zone 3: Fissure – kleine Stichflammen an der Wegkante
for n_, c in enumerate(PYRO_FISS):
    if n_ % 2 == 0:
        place("12_PYRO", "3062b", BLACK, [c], -HF[c] * PH - BH, BH)
        place("12_PYRO", "4589", TNORANGE, [c], -HF[c] * PH - 2 * BH, BH, studs=False)
    else: nozzle("12_PYRO", c, -HF[c] * PH)
# Zone 4: Feuerwerk-Racks im Innenraum an den Enden (MetLife: "fireworks nonstop")
RACKS = [(4, 12), (4, 48), (122, 12), (122, 48)]
for X, Y in RACKS:
    cc = [ik(X, Y), ik(X + 1, Y), ik(X, Y + 1), ik(X + 1, Y + 1), ik(X, Y + 2), ik(X + 1, Y + 2), ik(X, Y + 3), ik(X + 1, Y + 3)]
    if not floor_free(cc): continue
    FLOOR_USED.update(cc)
    i_ = min(c[0] for c in cc); k_ = min(c[1] for c in cc)
    place("12_PYRO", "3020", DBG, rect(i_, k_, 2, 4), -PH, PH, rot=90)
    for c in rect(i_, k_, 2, 4): place("12_PYRO", "3062b", BLACK, [c], -PH - BH, BH)

# =====================================================================================================
# 9. LASER und Strahler (10_LIGHTING)
# =====================================================================================================
for c in LASERS:
    y = -HF[c] * PH
    place("10_LIGHTING", "3062b", BLACK, [c], y - BH, BH)
    p = place("10_LIGHTING", "85861", BLACK, [c], y - BH - PH, PH)
    deco("10_LIGHTING", "30374", TGREEN, p.x, y - BH - PH - 4 - 80, p.z)       # Laserstrahl (Stab in offener Noppe)
# Bodenstrahler entlang der Wegkante: Rundplatte schwarz + Rundfliese trans-klar
for c in EDGE_LIGHTS:
    place("10_LIGHTING", "6141", BLACK, [c], -HF[c] * PH - PH, PH)
    place("10_LIGHTING", "98138", TCLEAR, [c], -HF[c] * PH - 2 * PH, PH, studs=False)

# =====================================================================================================
# 10. FINAL DETAILS: Freifallturm (MetLife), Faesser, Absperrung
# =====================================================================================================
DT = (113, 50)
dcells = rect(*ik(DT[0] + 3, DT[1]), 4, 4)
if floor_free(dcells):
    FLOOR_USED.update(dcells)
    pack("15_FINAL_DETAILS", dcells, DBG, -PH, PLATE, PH)
    core = rect(dcells[0][0] + 1, dcells[0][1] + 1, 2, 2)
    yy = -PH
    for g in range(26):
        if g == 9:                                    # Gondel-Ring (unten in Wartestellung), Sitze rundum
            place("15_FINAL_DETAILS", "3031", YELLOW, dcells, yy - PH, PH); yy -= PH
            for c in dcells:
                if c not in core: place("15_FINAL_DETAILS", "3070b", BLACK, [c], yy - PH, PH, studs=False)
        place("15_FINAL_DETAILS", "3941", WHITE if g % 4 else RED, core, yy - BH, BH); yy -= BH
    ytop = yy
    place("15_FINAL_DETAILS", "4032a", YELLOW, core, ytop - PH, PH)
    place("15_FINAL_DETAILS", "3062b", TRED, [core[0]], ytop - PH - BH, BH)
# Oelfaesser (Arena-Tour: "oil drum fixtures") auf Plaza und B-Stage
for c in DRUMS:
    if True:
        place("15_FINAL_DETAILS", "3062b", BLACK, [c], -12 * PH - BH, BH)
        place("15_FINAL_DETAILS", "98138", TNORANGE, [c], -12 * PH - BH - PH, PH, studs=False)


# =====================================================================================================
# 11. CHECKS
# =====================================================================================================
def checks():
    idx = defaultdict(list)
    for n, p in enumerate(parts):
        for c in p.studs: idx[(p.ytop, c)].append(n)
    adj = defaultdict(set)
    for n, p in enumerate(parts):
        for c in p.cells:
            for m in idx.get((p.ybot, c), []):
                if m != n: adj[n].add(m); adj[m].add(n)
    ground = {n for n, p in enumerate(parts) if p.name == "3811"}
    # Grundplatten untereinander verbunden (liegen auf dem Tisch nebeneinander; Verbund ueber Aufbauten)
    seen = set(ground); st = list(ground)
    while st:
        n = st.pop()
        for m in adj[n]:
            if m not in seen: seen.add(m); st.append(m)
    phys = [n for n, p in enumerate(parts) if p.cells and p.name != "3811"]
    loose = [n for n in phys if n not in seen]
    floating = [n for n in phys if not adj[n]]
    occ = {}; coll = []
    for n in phys:
        p = parts[n]; hit = False
        for c in p.cells:
            for yy in range(int(p.ytop), int(p.ybot), 2):
                if (c, yy) in occ and not hit: coll.append((occ[(c, yy)], n)); hit = True
                occ[(c, yy)] = n
    rep = {"teile": len(parts), "lose": len(loose), "schwebend": len(floating), "kollisionen": len(coll)}
    print("Pruefung:", rep)
    for n in (loose + floating)[:12]:
        p = parts[n]; print("  !", p.sub, p.name, p.color, sorted(p.cells)[:2], p.ytop, p.ybot)
    for a, b in coll[:12]:
        print("  X", parts[a].sub, parts[a].name, parts[a].ytop, sorted(parts[a].cells)[:2], "<->",
              parts[b].sub, parts[b].name, parts[b].ytop, sorted(parts[b].cells)[:2])
    return rep


def export(rep):
    subs = [s for s in SUBS if any(p.sub == s for p in parts)]
    out = [f"0 FILE {NAME}.ldr", "0 Travis Scott - UTOPIA - Circus Maximus Tour - MetLife Stadium 2024 (LEGO MOC)",
           f"0 Name: {NAME}.ldr", "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""]
    for s in subs:
        out += [f"0 // {SUBS[s]}", f"1 16 0 0 0 {mstr(RM[0])} {s}.ldr"]
    out += ["0 NOFILE"]
    for s in subs:
        body = [p.line() for p in parts if p.sub == s and p.export]
        body += [f"1 16 {fmt(x)} {fmt(y)} {fmt(z)} {mstr(RM[r])} {m}.ldr" for sb, m, x, y, z, r in refs if sb == s]
        out += [f"0 FILE {s}.ldr", f"0 {SUBS[s]}", f"0 Name: {s}.ldr"] + body + ["0 NOFILE"]
    for m in MASTERS:
        title = SUBS.get(m, "Hebeplattform Zustand 1 (unten) - alternativ zu 13_LIFT")
        out += [f"0 FILE {m}.ldr", f"0 {title}", f"0 Name: {m}.ldr"] + [p.line() for p in local[m]] + ["0 NOFILE"]
    open(os.path.join(HERE, f"{NAME}.mpd"), "w").write("\n".join(out) + "\n")
    # Stueckliste: alle Weltteile (Kopf-Instanzen mitgezaehlt), ohne Lift-Zustand 1
    bom = Counter((p.name, p.color) for p in parts)
    rows = ["LDraw Part,BrickLink ID,Farbe,Menge"]; xml = ["<INVENTORY>"]
    for (nm, c), q in sorted(bom.items()):
        bl = BL_ID.get(nm, nm); cn, blc = COLORS[c]
        rows.append(f"{nm}.dat,{bl},{cn},{q}")
        xml.append(f"<ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID><COLOR>{blc}</COLOR><MINQTY>{q}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    open(os.path.join(HERE, f"{NAME}_bom.csv"), "w").write("\n".join(rows) + "\n")
    open(os.path.join(HERE, f"{NAME}_bricklink.xml"), "w").write("\n".join(xml) + "\n")
    # Layout fuer Blueprint/Ansichten
    lay = {"cells": [[*XY(c), HF[c], KIND[c], MOD[c]] for c in HF],
           "heads": [[m, X0_, Y0_, Wd, Dp, rot, ph] for m, X0_, Y0_, Wd, Dp, rot, ph in HEADS],
           "lift": [list(XY(c)) for c in LIFT], "pyro_a": [list(XY(c)) for c in PYRO_A],
           "pyro_ridge": [list(XY(c)) for c in PYRO_RIDGE], "pyro_fiss": [list(XY(c)) for c in PYRO_FISS],
           "lasers": [list(XY(c)) for c in LASERS], "racks": RACKS, "leds": LEDS, "led_w": LED_W,
           "light_towers": LIGHT_TOWERS, "speakers": SPEAKERS, "foh": [list(XY(c)) for c in FOH],
           "drop_tower": list(DT), "check": rep,
           "occ": [[p.sub, [list(XY(c)) for c in p.cells], p.ytop, p.ybot] for p in parts if p.cells and p.name != "3811"]}
    json.dump(lay, open(os.path.join(HERE, "layout.json"), "w"))
    total = sum(bom.values())
    print("Teile gesamt:", total, "| Positionen:", len(bom))
    for s in subs: print(f"  {s}: {sum(1 for p in parts if p.sub == s)}")
    return total


rep = checks()
export(rep)
print("CHECK", "OK" if rep["lose"] + rep["schwebend"] + rep["kollisionen"] == 0 else "FEHLER")
