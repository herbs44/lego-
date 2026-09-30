"""
Kanye West – My Beautiful Dark Twisted Fantasy – Diorama "Runaway" (LEGO MOC Generator)
48x48-Grundplatte. Rueckwand = 3D-Relief (48x48 Noppen, per SNOT hochkant an einer Tragwand): rotes Stofffeld wie
das Cover, darin das Ballerina-Gemaelde (30x30) im erhabenen Goldrahmen. Davor die Runaway-Szene mit Minifiguren:
weisses Podest mit schwarzem Fluegel und Kanye im roten Anzug, ein Halbkreis Ballerinen mit Dutt, die lange weisse
Dinnertafel mit Gaesten in Weiss, am Kopfende der Phoenix; Schachbrettboden, roter Laeufer, goldene Standleuchter.
Pipeline: Relief (make_relief) -> Tragwand + SNOT -> Zellen/Ebenen -> Packing -> Minifiguren -> Checks -> MPD/BOM/XML

Aufruf: python3 generate_mbdtf_diorama.py
  Das Wandrelief (wand_relief.mpd) wird vorher mit tools/relief/make_relief.py erzeugt (Befehl im README).
"""
import math, os, random, re
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
NAME = "mbdtf_diorama"
random.seed(5)

LDU, BH, PH = 20, 24, 8
RM = {0: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 90: [[0, 0, -1], [0, 1, 0], [1, 0, 0]],
      180: [[-1, 0, 0], [0, 1, 0], [0, 0, -1]], 270: [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]}

# ---------------- Farben (LDraw: Name, BrickLink-ID) ----------------
BLACK, WHITE, RED, DKRED, GOLD, LNOUGAT, MNOUGAT, RBROWN, ORANGE, TCLEAR, TYELLOW, DKBROWN, TAN = \
    0, 15, 4, 320, 297, 78, 84, 70, 25, 47, 46, 308, 19
COLORS = {0: ("Black", 11), 15: ("White", 1), 4: ("Red", 5), 320: ("Dark Red", 59), 297: ("Pearl Gold", 115),
          78: ("Light Nougat", 90), 84: ("Medium Nougat", 150), 70: ("Reddish Brown", 88), 25: ("Orange", 4),
          47: ("Trans-Clear", 12), 46: ("Trans-Yellow", 19), 308: ("Dark Brown", 120), 19: ("Tan", 2)}

# ---------------- Teile ----------------
BRICK = {(1, 1): "3005", (1, 2): "3004", (1, 3): "3622", (1, 4): "3010", (1, 6): "3009", (1, 8): "3008",
         (2, 2): "3003", (2, 4): "3001"}
PLATE = {(1, 1): "3024", (1, 2): "3023", (1, 3): "3623", (1, 4): "3710", (1, 6): "3666", (1, 8): "3460",
         (2, 2): "3022", (2, 3): "3021", (2, 4): "3020", (2, 6): "3795", (2, 8): "3034",
         (4, 4): "3031", (4, 6): "3032", (4, 8): "3035"}
TILE = {(1, 1): "3070b", (1, 2): "3069b", (1, 4): "2431", (1, 6): "6636", (1, 8): "4162",
        (2, 2): "3068b", (2, 4): "87079"}
TILE1 = {k: v for k, v in TILE.items() if k[0] == 1}
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "3062b": "3062", "6141": "4073",
         "3815c01": "970c00", "3815c02": "970c00", "3626bp01": "3626c", "3626bp02": "3626c"}
TITLES = {"wand": "Tragwand mit SNOT-Steinen, Sockel", "wand_relief": "Wandrelief: rotes Tuch und Gemaelde (48x48)",
          "boden": "Grundplatte, Schachbrettboden, roter Laeufer", "podest": "Podest mit Fluegel",
          "kanye": "Kanye am Fluegel", "ballerinen": "Ballerinen (Minifiguren)",
          "tafel": "Runaway-Dinnertafel", "gaeste": "Gaeste und Phoenix", "leuchter": "Standleuchter"}


def fmt(v):
    v = round(v, 3)
    return str(int(v)) if v == int(v) else str(v)


def mstr(M): return " ".join(fmt(round(v, 4)) for r in M for v in r)
def mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mv(M, v): return [sum(M[i][k] * v[k] for k in range(3)) for i in range(3)]


class Part:
    __slots__ = ("sub", "name", "color", "x", "y", "z", "M", "cells", "ytop", "ybot", "studs")

    def __init__(s, sub, name, color, x, y, z, M, cells, ytop, ybot, studs=True):
        s.sub, s.name, s.color, s.x, s.y, s.z, s.M = sub, name, color, x, y, z, M
        s.cells, s.ytop, s.ybot = frozenset(cells), ytop, ybot
        s.studs = frozenset(cells) if studs else frozenset()

    def line(s):
        return f"1 {s.color} {fmt(s.x)} {fmt(s.y)} {fmt(s.z)} {mstr(s.M)} {s.name}.dat"


parts = []


def rect(i0, k0, nx, nz): return [(i, k) for i in range(i0, i0 + nx) for k in range(k0, k0 + nz)]


def place(sub, name, color, cells, ytop, h, studs=True, rot=None, y=None):
    """Teil ueber Zellen (Ursprung oben, Mitte der Grundflaeche). rot None: lange Seite bestimmt die Drehung."""
    xs = [c[0] for c in cells]; zs = [c[1] for c in cells]
    nx, nz = max(xs) - min(xs) + 1, max(zs) - min(zs) + 1
    if rot is None: rot = 90 if nz > nx else 0
    x = (min(xs) + max(xs) + 1) / 2 * LDU; z = (min(zs) + max(zs) + 1) / 2 * LDU
    p = Part(sub, name, color, x, ytop if y is None else y, z, RM[rot], cells, ytop, ytop + h, studs)
    parts.append(p); return p


def pack(sub, cells, color, ytop, table, h, studs=True, prefer_x=True, colfn=None):
    """Gleichfarbige Rechtecke, groesste zuerst; prefer_x = lange Seite entlang x (Verband wechselt je Lage)."""
    todo = set(cells)
    sizes = sorted(table, key=lambda s: -s[0] * s[1])
    for c in sorted(cells, key=lambda c: (c[1], c[0]) if prefer_x else (c[0], c[1])):
        if c not in todo: continue
        col = colfn(c) if colfn else color
        for a, b in sizes:
            done = False
            for nx, nz in (((b, a), (a, b)) if prefer_x else ((a, b), (b, a))):
                rc = rect(c[0], c[1], nx, nz)
                if all(q in todo and (not colfn or colfn(q) == col) for q in rc):
                    place(sub, table[(a, b)], col, rc, ytop, h, studs); todo -= set(rc); done = True; break
            if done: break


def runs_1d(xs, start_off):
    """Laeufer-Verband in einer Reihe: 1x4-Steine, Versatz start_off (0/2), Reste 1x1-1x3."""
    out, xs = [], sorted(xs)
    seg = []
    for x in xs + [None]:
        if seg and (x is None or x != seg[-1] + 1):
            i = 0
            first = start_off if len(seg) > 4 else 0
            if first: out.append((seg[0], first)); i = first
            while i < len(seg):
                n = min(4, len(seg) - i); out.append((seg[i], n)); i += n
            seg = []
        if x is not None: seg.append(x)
    return out


# ================= Grundriss =================
# Zellen i (x) und k (z) von -24..23. Hinten = -z (Wand), vorne = +z (Betrachter). Von vorne liegt +x LINKS.
N = 24
ALL = rect(-N, -N, 2 * N, 2 * N)
parts.append(Part("boden", "4186", BLACK, 0, 0, 0, RM[0], ALL, 0, 4))

# ================= Wandrelief (hochkant) und Tragwand =================
# Relief lokal: Noppen nach -y, Bild oben = -z, Bild links = +x.  Welt: Noppen nach +z (zum Betrachter),
# Bild oben = -y.  Matrix: x' = x, y' = z + TY, z' = -y + TZ.
WALL_K = -N                                  # Tragwand 1 tief
Z_WALL_FRONT = (WALL_K + 1) * LDU            # -460
TZ = Z_WALL_FRONT + 8                        # Unterseite der 16x16-Platten liegt an der Wand
Y_PANEL_BOT = -98                            # Unterkante Relief (unterste Reihe Mitte = -108 = Steinmitte Lage 4)
TY = Y_PANEL_BOT - 480
R_WALL = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]
relief_lines = []
for L in open(os.path.join(HERE, "wand_relief.mpd")):
    p = L.split()
    if p and p[0] == "1" and p[-1] != "4186.dat": relief_lines.append(L.rstrip())
for px in (-320, 0, 320):                    # statt Baseplate: 9 Platten 16x16 (haben Unterseite fuer SNOT-Noppen)
    for pz in (-320, 0, 320): relief_lines.append(f"1 0 {px} 0 {pz} 1 0 0 0 1 0 0 0 1 91405.dat")

# Tiefe des Reliefs je (Spalte i, Hoehenzeile) fuer den Kollisionscheck mit der Szene
relief_front = defaultdict(lambda: -1e9)
for L in relief_lines:
    p = L.split(); lx, ly, lz = float(p[2]), float(p[3]), float(p[4])
    wx, wy, wz = lx, lz + TY, -ly + TZ + 4
    ci = math.floor(wx / LDU); r = math.floor(wy / LDU)
    relief_front[(ci, r)] = max(relief_front[(ci, r)], wz)

WALL_G = 45                                  # 1080 LDU, Relief-Oberkante bei -1058
SNOT_ROWS = [4 + 5 * j for j in range(8)]    # Lagen, deren Steinmitte auf einer Reliefreihe liegt
SNOT_COLS = [23 - c for c in (2, 6, 9, 13, 18, 22, 25, 29, 34, 38, 41, 45)]
snot = set()
for n in SNOT_ROWS:
    ys = -(n * BH + 12)
    assert abs(((Y_PANEL_BOT - ys) - 10) % 20) < 1e-6, (n, ys)
    for i in SNOT_COLS: snot.add((i, n))
for g in range(WALL_G):
    yt = -(g + 1) * BH
    xs = [i for i in range(-N, N) if (i, g) not in snot]
    for i0, n in runs_1d(xs, 2 if g % 2 else 0):
        place("wand", BRICK[(1, n)], BLACK, rect(i0, WALL_K, n, 1), yt, BH)
    for i in [i for i in range(-N, N) if (i, g) in snot]:
        place("wand", "87087", BLACK, [(i, WALL_K)], yt, BH, rot=180)       # Seitennoppe nach vorne (+z)
pack("wand", rect(-N, WALL_K, 2 * N, 1), GOLD, -WALL_G * BH - PH, TILE1, PH, studs=False)

# Sockel vor der Wand (dunkelrot, 3 Steine) mit Goldleiste
DADO_K = WALL_K + 1
for g in range(3):
    for i0, n in runs_1d(list(range(-N, N)), 2 if g % 2 else 0):
        place("wand", BRICK[(1, n)], DKRED, rect(i0, DADO_K, n, 1), -(g + 1) * BH, BH)
pack("wand", rect(-N, DADO_K, 2 * N, 1), GOLD, -3 * BH - PH, TILE1, PH, studs=False)

# ================= Szene: reservierte Zellen =================
FLOOR = {c for c in ALL if c[1] > DADO_K}
reserved = set()

# ---- Podest (weiss, Goldrand) ----
PC = (0.0, -8.0)
PODEST = {c for c in FLOOR if math.hypot(c[0] + 0.5 - PC[0], c[1] + 0.5 - PC[1]) <= 5.4}
RIM = {c for c in PODEST if any((c[0] + a, c[1] + b) not in PODEST for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
reserved |= PODEST
pack("podest", PODEST, WHITE, -PH, PLATE, PH, prefer_x=True)
pack("podest", PODEST, WHITE, -2 * PH, PLATE, PH, prefer_x=False)
YP = -2 * PH                                  # Noppen-Oberkante Podest

# Fluegel (schwarz), Tastatur zum Pianisten (-z), Korpus zum Betrachter
PIANO = rect(-2, -10, 4, 6)
PLEGS = [(-2, -10), (1, -10), (-2, -5), (1, -5)]
for c in PLEGS:
    for g in range(2): place("podest", "3062b", BLACK, [c], YP - (g + 1) * BH, BH)
yb = YP - 2 * BH
place("podest", PLATE[(4, 6)], BLACK, PIANO, yb - PH, PH, rot=90); yb -= PH                     # Boden -72
place("podest", TILE[(1, 4)], WHITE, rect(-2, -10, 4, 1), yb - PH, PH, studs=False)             # Tasten
ring = [c for c in rect(-2, -9, 4, 5) if c[0] in (-2, 1) or c[1] in (-9, -5)]
pack("podest", ring, BLACK, yb - BH, BRICK, BH)
top = rect(-2, -9, 4, 5)
pack("podest", top, BLACK, yb - BH - PH, PLATE, PH, prefer_x=False)
CANDLE_P = (1, -5)
pack("podest", [c for c in top if c != CANDLE_P and c != (-2, -9)], BLACK, yb - BH - 2 * PH, TILE, PH, studs=False)
yl = yb - BH - PH
# Notenpult: goldene Fliese hochkant waere SNOT; hier als Kerzenleuchter auf dem Fluegel (Liberace-Detail)
place("podest", "6141", GOLD, [CANDLE_P], yl - PH, PH)
place("podest", "3062b", GOLD, [CANDLE_P], yl - PH - BH, BH)
place("podest", "6141", WHITE, [CANDLE_P], yl - 2 * PH - BH, PH)
place("podest", "15470", TYELLOW, [CANDLE_P], yl - 2 * PH - BH - 18, 18, studs=False, y=yl - 2 * PH - BH)
place("podest", "2343", GOLD, [(-2, -9)], yl - 40, 40, studs=False, y=yl - 40)                  # Kelch auf dem Fluegel
# Bank
BENCH = [(-1, -12), (0, -12)]
place("podest", BRICK[(1, 2)], BLACK, BENCH, YP - BH, BH)
place("podest", PLATE[(1, 2)], BLACK, BENCH, YP - BH - PH, PH)
pack("podest", PODEST - set(PLEGS) - set(BENCH), None, YP - PH, TILE, PH, studs=False,
     colfn=lambda c: GOLD if c in RIM else WHITE)


# ================= Minifiguren =================
def rx(deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[1, 0, 0], [0, c, -s_], [0, s_, c]]


I3 = RM[0]


def minifig(sub, cells, surf_y, rot, torso, legs_col, head_col, arms=(0, 0), arm_col=None, hair=None,
            head="3626bp01", legs="3815c01", sitting=False):
    """Minifigur auf 'cells' (2 Zellen), Blick lokal nach -z; rot 180 = zum Betrachter. arms = Hebewinkel."""
    M = RM[rot]
    cx = sum((c[0] + 0.5) * LDU for c in cells) / 2; cz = sum((c[1] + 0.5) * LDU for c in cells) / 2
    P = [cx, surf_y - (53 if sitting else 72), cz]
    arm_col = torso if arm_col is None else arm_col
    comps = [(head, head_col, (0, -24, 0), I3), ("973", torso, (0, 0, 0), I3), (legs, legs_col, (0, 32, 0), I3)]
    for sgn, arm, a in ((-1, "3818", arms[0]), (1, "3819", arms[1])):
        A0 = [[0.985, -sgn * 0.174, 0], [sgn * 0.174, 0.985, 0], [0, 0, 1]]
        H0 = [[0.985, -sgn * 0.174, 0], [-sgn * -0.133, 0.754, -0.643], [-sgn * -0.112, 0.633, 0.766]]
        piv = (sgn * 15.552, 9, 0); hand = (sgn * 23.1, 24.7, -10)
        R = rx(a)
        rel = mv(R, [hand[i] - piv[i] for i in range(3)])
        comps.append((arm, arm_col, piv, mm(R, A0)))
        comps.append(("3820", head_col, tuple(piv[i] + rel[i] for i in range(3)), mm(R, H0)))
    if hair: comps.append((hair[0], hair[1], (0, -24, 0), I3))
    for nm, col, off, Mi in comps:
        w = mv(M, off); pos = [P[0] + w[0], P[1] + w[1], P[2] + w[2]]
        is_legs = nm == legs
        parts.append(Part(sub, nm, col, pos[0], pos[1], pos[2], mm(M, Mi), cells if is_legs else [],
                          surf_y - (21 if sitting else 40) if is_legs else 0, surf_y if is_legs else 0, studs=False))


# ---- Kanye am Fluegel: roter Anzug, sitzt auf der Bank, Blick zum Betrachter ----
minifig("kanye", BENCH, YP - BH - PH, 180, RED, RED, RBROWN, arms=(-55, -55), hair=("3901", BLACK), sitting=True,
        legs="3815c02")

# ---- Ballerinen: Halbkreis vor dem Podest, Dutt, schwarzes Tutu (glockenfoermig, 36036) ----
SKIN = [LNOUGAT, MNOUGAT, RBROWN, LNOUGAT, MNOUGAT, RBROWN, LNOUGAT, MNOUGAT, LNOUGAT, RBROWN, LNOUGAT] * 2
BALL = [(-13, -6, (-165, -165)), (-11, -1, (-90, -165)), (-7, 3, (-165, -40)), (-3, 6, (-165, -165)),
        (2, 6, (-120, -120)), (6, 3, (-40, -165)), (10, -1, (-165, -90)), (12, -6, (-165, -165)),
        (-1, 11, (-90, -90)),
        # Formation vorne (Runaway: viele Ballerinen), zwei versetzte Reihen
        (-17, 9, (-165, -165)), (-12, 10, (-120, -165)), (-7, 10, (-165, -120)), (5, 10, (-120, -165)),
        (10, 10, (-165, -120)), (15, 9, (-165, -165)),
        (-15, 15, (-90, -165)), (-10, 16, (-165, -165)), (-5, 16, (-165, -90)), (3, 16, (-90, -165)),
        (8, 16, (-165, -165)), (13, 15, (-165, -90))]
CARPET = {c for c in FLOOR if -3 <= c[0] <= 2 and c[1] >= -3 and c[1] < N - 1 and c not in PODEST}
for n_, (i, k, arms) in enumerate(BALL):
    cells = [(i, k), (i + 1, k)]
    reserved |= set(cells)
    base = DKRED if all(c in CARPET for c in cells) else BLACK
    place("ballerinen", PLATE[(1, 2)], base, cells, -PH, PH)
    minifig("ballerinen", cells, -PH, 180, BLACK, BLACK, SKIN[n_], arms=arms, arm_col=SKIN[n_],
            hair=("99240", BLACK), head="3626bp02", legs="36036")

# ================= Runaway-Dinnertafel =================
T_I = (-20, -19)
T_K = (-16, -1)
TABLE = rect(T_I[0], T_K[0], 2, T_K[1] - T_K[0] + 1)
TLEGS = [(-20, -16), (-19, -16), (-20, -1), (-19, -1), (-20, -9), (-19, -8)]
for c in TLEGS:
    for g in range(2): place("tafel", "3062b", WHITE, [c], -(g + 1) * BH, BH)
place("tafel", PLATE[(2, 8)], WHITE, rect(-20, -16, 2, 8), -2 * BH - PH, PH)
place("tafel", PLATE[(2, 8)], WHITE, rect(-20, -8, 2, 8), -2 * BH - PH, PH)
YT = -2 * BH - PH                              # Tischplatte Noppen
items = {}
SEATS = [-15, -12, -9, -6, -3]                 # Stuhlpaare (k, k+1) auf beiden Seiten
GUESTS = []
for side, (seat_i, back_i, rot, tcell) in enumerate(((-18, -17, 270, -19), (-21, -22, 90, -20))):
    for n_, k0 in enumerate(SEATS):
        seat = [(seat_i, k0), (seat_i, k0 + 1)]
        back = [(back_i, k0), (back_i, k0 + 1)]
        reserved |= set(seat) | set(back)
        place("tafel", BRICK[(1, 2)], GOLD, seat, -BH, BH)
        place("tafel", PLATE[(1, 2)], DKRED, seat, -BH - PH, PH)
        for g in range(2): place("tafel", BRICK[(1, 2)], GOLD, back, -(g + 1) * BH, BH)
        place("tafel", TILE[(1, 2)], GOLD, back, -2 * BH - PH, PH, studs=False)
        GUESTS.append((seat, rot))
        items[(tcell, k0)] = "kelch"; items[(tcell, k0 + 1)] = "teller"
for k in (-13, -10, -7, -4):
    items[(-20 if k % 2 else -19, k)] = "leuchter"
items[(-20, -16)] = "kelch"; items[(-19, -16)] = "teller"
items[(-20, -1)] = "leuchter"; items[(-19, -1)] = "leuchter"
for c, what in items.items():
    if what == "teller": place("tafel", "98138", WHITE, [c], YT - PH, PH, studs=False)
    elif what == "kelch": place("tafel", "2343", GOLD, [c], YT - 40, 40, studs=False, y=YT - 40)
    elif what == "leuchter":
        for g in range(2): place("tafel", "3062b", GOLD, [c], YT - (g + 1) * BH, BH)
        place("tafel", "6141", WHITE, [c], YT - 2 * BH - PH, PH)
        place("tafel", "15470", TYELLOW, [c], YT - 2 * BH - PH - 18, 18, studs=False, y=YT - 2 * BH - PH)
pack("tafel", [c for c in TABLE if c not in items], WHITE, YT - PH, TILE, PH, studs=False)
reserved |= set(TLEGS)

# Gaeste in Weiss (verschiedene Hauttoene und Frisuren)
HAIRS = [("3901", BLACK), ("99240", DKBROWN), ("92081", BLACK), ("20877", TAN), ("3901", DKBROWN),
         ("26139", BLACK), ("99240", BLACK), ("21268", DKBROWN), ("62696", BLACK), ("40240", BLACK)]
for n_, (seat, rot) in enumerate(GUESTS):
    hair = HAIRS[n_ % len(HAIRS)]
    female = hair[0] in ("99240", "20877", "62696")
    minifig("gaeste", seat, -BH - PH, rot, WHITE, WHITE, SKIN[(n_ * 4) % len(SKIN)], arms=(-35, -35),
            hair=hair, head="3626bp02" if female else "3626bp01", legs="3815c02", sitting=True)
# Phoenix am Kopfende (Blick die Tafel entlang, +z): orange, rotes Haar
PSEAT = [(-20, -17), (-19, -17)]
PBACK = [(-20, -18), (-19, -18)]
reserved |= set(PSEAT) | set(PBACK)
place("gaeste", BRICK[(1, 2)], GOLD, PSEAT, -BH, BH)
place("gaeste", PLATE[(1, 2)], DKRED, PSEAT, -BH - PH, PH)
for g in range(3): place("gaeste", BRICK[(1, 2)], GOLD, PBACK, -(g + 1) * BH, BH)
yw = -3 * BH
for c, rot, wrot in ((PBACK[0], 0, 270), (PBACK[1], 0, 90)):          # Clip nach hinten, Fluegel nach aussen
    cp = place("gaeste", "60897", GOLD, [c], yw - PH, PH, rot=rot)
    parts.append(Part("gaeste", "11100", RED, cp.x, yw - PH + 2, cp.z - 17, RM[wrot], [], 0, 0, studs=False))
minifig("gaeste", PSEAT, -BH - PH, 180, ORANGE, ORANGE, MNOUGAT, arms=(-20, -80), hair=("20595", RED),
        head="3626bp02", legs="3815c02", sitting=True)

# ================= Standleuchter =================
CANDLES = [(13, -16), (-14, -16), (21, 18), (-22, 18)]
for c in CANDLES:
    reserved.add(c)
    place("leuchter", "6141", GOLD, [c], -PH, PH)
    for g in range(7): place("leuchter", "3062b", GOLD, [c], -PH - (g + 1) * BH, BH)
    yc = -PH - 7 * BH
    place("leuchter", "6141", WHITE, [c], yc - PH, PH)
    place("leuchter", "15470", TYELLOW, [c], yc - PH - 18, 18, studs=False, y=yc - PH)

# ================= Boden: Schachbrett, roter Laeufer, Goldschild =================
PLAQUE = set(rect(-3, N - 1, 6, 1))
BORDER = {c for c in FLOOR if c[1] == N - 1}
floor = FLOOR - reserved


def fcol(c):
    if c in BORDER: return GOLD if c in PLAQUE else BLACK
    if c in CARPET: return GOLD if c[0] in (-3, 2) else DKRED
    return BLACK if ((c[0] // 2) + (c[1] // 2)) % 2 == 0 else WHITE


rest = set(floor)
for c in sorted(floor):
    if c[0] % 2 == 0 and c[1] % 2 == 0:
        blk = rect(c[0], c[1], 2, 2)
        if all(q in rest and fcol(q) == fcol(c) for q in blk):
            place("boden", TILE[(2, 2)], fcol(c), blk, -PH, PH, studs=False); rest -= set(blk)
pack("boden", rest, None, -PH, TILE1, PH, studs=False, colfn=fcol, prefer_x=False)


# ================= Checks =================
def checks():
    idx = defaultdict(list)
    for n, p in enumerate(parts):
        for c in p.studs: idx[(p.ytop, c)].append(n)
    adj = defaultdict(set); below = defaultdict(set)
    for n, p in enumerate(parts):
        for c in p.cells:
            for m in idx.get((p.ybot, c), []):
                if m != n: below[n].add(m); adj[n].add(m); adj[m].add(n)
    seen = {0}; st = [0]
    while st:
        n = st.pop()
        for m in adj[n]:
            if m not in seen: seen.add(m); st.append(m)
    phys = [n for n, p in enumerate(parts) if p.cells]
    loose = [n for n in phys if n not in seen]
    floating = [n for n in phys[1:] if not below[n]]
    occ = {}; coll = []
    for n in phys[1:]:
        p = parts[n]; hit = False
        for c in p.cells:
            for yy in range(int(p.ytop), int(p.ybot), 2):
                if (c, yy) in occ and not hit: coll.append((occ[(c, yy)], n)); hit = True
                occ[(c, yy)] = n
    # Relief ragt nach vorne: Szene darf nicht hineinragen
    rcoll = []
    for n in phys[1:]:
        p = parts[n]
        if p.sub == "wand": continue
        for c in p.cells:
            for r in range(math.floor(p.ytop / LDU), math.floor((p.ybot - 1) / LDU) + 1):
                if relief_front[(c[0], r)] > c[1] * LDU: rcoll.append(n); break
            else: continue
            break
    print("Teile (Szene):", len(parts), "| lose:", len(loose), "| schwebend:", len(floating),
          "| Kollisionen:", len(coll), "| in das Relief ragend:", len(rcoll), "| SNOT-Noppen:", len(snot))
    for n in (loose + floating + rcoll)[:12]:
        p = parts[n]; print("  !", p.sub, p.name, p.color, p.x, p.y, p.z)
    for a, b in coll[:12]:
        print("  X", parts[a].sub, parts[a].name, parts[a].ytop, sorted(parts[a].cells)[:2], "<->",
              parts[b].sub, parts[b].name, parts[b].ytop, sorted(parts[b].cells)[:2])
    return len(loose) + len(floating) + len(coll) + len(rcoll)


def relief_colors():
    import sys
    sys.path.insert(0, os.path.join(HERE, "..", "tools", "relief"))
    import make_relief as mr
    return {v[1]: v[0] for v in list(mr.PALETTE.values()) + list(mr.EXTRA.values())}


RELIEF_COLORS = relief_colors()


def export():
    order = [s for s in TITLES if s == "wand_relief" or any(p.sub == s for p in parts)]
    out = [f"0 FILE {NAME}.ldr", "0 Kanye West - My Beautiful Dark Twisted Fantasy - Diorama Runaway",
           f"0 Name: {NAME}.ldr", "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""]
    for s in order:
        if s == "wand_relief": out += [f"0 // {TITLES[s]}", f"1 16 0 {TY} {TZ} {mstr(R_WALL)} {s}.ldr"]
        else: out += [f"0 // {TITLES[s]}", f"1 16 0 0 0 {mstr(RM[0])} {s}.ldr"]
    out += ["0 NOFILE"]
    for s in order:
        body = relief_lines if s == "wand_relief" else [p.line() for p in parts if p.sub == s]
        out += [f"0 FILE {s}.ldr", f"0 {TITLES[s]}", f"0 Name: {s}.ldr"] + body + ["0 NOFILE"]
    open(os.path.join(OUT, f"{NAME}.mpd"), "w").write("\n".join(out) + "\n")
    # Stueckliste: Szene + Relief (Relief-Farben ueber dessen Stueckliste)
    bom = Counter()
    for p in parts: bom[(p.name, COLORS[p.color][0], COLORS[p.color][1])] += 1
    rx_ = open(os.path.join(HERE, "wand_relief_bricklink.xml")).read()
    for m in re.finditer(r"<ITEMID>([^<]+)</ITEMID><COLOR>(\d+)</COLOR><MINQTY>(\d+)</MINQTY>", rx_):
        pid, blc, q = m.group(1), int(m.group(2)), int(m.group(3))
        if pid == "4186": pid, q = "91405", 9
        cname = next((v[0] for v in COLORS.values() if v[1] == blc), None) or RELIEF_COLORS.get(blc)
        bom[("BL:" + pid, cname or f"BL-Farbe {blc}", blc)] += q
    rows = ["LDraw/BrickLink,BrickLink ID,Farbe,Menge"]; xml = ["<INVENTORY>"]
    merged = Counter()
    for (nm, cn, blc), q in bom.items():
        bl = nm[3:] if nm.startswith("BL:") else BL_ID.get(nm, nm)
        merged[(bl, cn, blc)] += q
    for (bl, cn, blc), q in sorted(merged.items()):
        rows.append(f"{bl},{bl},{cn},{q}")
        xml.append(f"<ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID><COLOR>{blc}</COLOR><MINQTY>{q}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    open(os.path.join(OUT, f"{NAME}_bom.csv"), "w").write("\n".join(rows) + "\n")
    open(os.path.join(OUT, f"{NAME}_bricklink.xml"), "w").write("\n".join(xml) + "\n")
    print("Teile gesamt:", sum(merged.values()), "| Positionen:", len(merged))
    for s in order:
        print(f"  {s}: {len(relief_lines) if s == 'wand_relief' else sum(1 for p in parts if p.sub == s)}")


bad = checks()
export()
print("CHECK", "OK" if bad == 0 else f"FEHLER ({bad})")
