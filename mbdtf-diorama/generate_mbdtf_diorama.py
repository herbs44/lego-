"""
Kanye West – My Beautiful Dark Twisted Fantasy – Diorama "The Ballerina Room" (LEGO MOC Generator)
Rotes Zimmer mit Schachbrettboden, an der Wand das Ballerina-Gemaelde im gestuften Goldrahmen (Pixelbild aus
1x1-Platten, seitlich sichtbar). Davor steigt die Ballerina als gebaute 3D-Figur aus dem Bild: schwarzes Tutu,
Maske, Weinglas in der ausgestreckten Hand, auf einem tuerkisen Podest. Rechts die weisse "Runaway"-Dinnertafel.
Keine Minifiguren. Massstab: 1 Baseplate 32x32.
Pipeline: Zellen/Ebenen -> Packing (Verband) -> Figuren/Details -> Checks (lose/schwebend/Kollision) -> MPD/BOM/XML

Aufruf: python3 generate_mbdtf_diorama.py [cover.png]
  Mit Cover (250 px, Gemaelde bei Pixel 70-179) wird das Gemaelde neu gerastert und in gemaelde.json gespeichert;
  ohne Cover wird gemaelde.json aus dem Repo benutzt (das Cover selbst liegt nicht im Repo).
"""
import json, math, os, random, sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
NAME = "mbdtf_diorama"
random.seed(5)

LDU, BH, PH = 20, 24, 8
ROT = {0: "1 0 0 0 1 0 0 0 1", 90: "0 0 -1 0 1 0 1 0 0"}

# ---------------- Farben (LDraw: Name, BrickLink-ID) ----------------
BLACK, WHITE, RED, DKRED, GOLD, LNOUGAT, DKTURQ, TCLEAR, TRED, TYELLOW, SILVER, DKGREEN = \
    0, 15, 4, 320, 297, 78, 3, 47, 36, 46, 179, 288
COLORS = {0: ("Black", 11), 15: ("White", 1), 4: ("Red", 5), 320: ("Dark Red", 59), 297: ("Pearl Gold", 115),
          78: ("Light Nougat", 90), 3: ("Dark Turquoise", 39), 47: ("Trans-Clear", 12), 36: ("Trans-Red", 17),
          46: ("Trans-Yellow", 19), 179: ("Flat Silver", 95), 288: ("Dark Green", 80)}

# ---------------- Teile ----------------
BRICK = {(1, 1): "3005", (1, 2): "3004", (1, 3): "3622", (1, 4): "3010", (1, 6): "3009", (1, 8): "3008",
         (2, 2): "3003", (2, 3): "3002", (2, 4): "3001", (2, 6): "2456", (2, 8): "3007"}
PLATE = {(1, 1): "3024", (1, 2): "3023", (1, 3): "3623", (1, 4): "3710", (1, 6): "3666", (1, 8): "3460",
         (2, 2): "3022", (2, 3): "3021", (2, 4): "3020", (2, 6): "3795", (2, 8): "3034", (2, 10): "3832",
         (4, 4): "3031", (4, 6): "3032", (4, 8): "3035"}
TILE = {(1, 1): "3070b", (1, 2): "3069b", (1, 4): "2431", (1, 6): "6636", (1, 8): "4162",
        (2, 2): "3068b", (2, 4): "87079"}
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "3062b": "3062", "6141": "4073", "4032a": "4032"}
TITLES = {"boden": "Grundplatte und Schachbrettboden", "wand": "Rote Waende mit Sockel und Goldleiste",
          "rahmen": "Goldrahmen", "gemaelde": "Gemaelde (Ballerina, Pixelbild aus 1x1-Platten)",
          "podest": "Podest", "ballerina": "Ballerina (3D-Figur mit Weinglas)", "tafel": "Runaway-Dinnertafel"}


class Part:
    __slots__ = ("sub", "name", "color", "x", "y", "z", "rot", "cells", "ytop", "ybot", "studs")

    def __init__(s, sub, name, color, x, y, z, rot, cells, ytop, ybot, studs=True):
        s.sub, s.name, s.color, s.x, s.y, s.z, s.rot = sub, name, color, x, y, z, rot
        s.cells, s.ytop, s.ybot = frozenset(cells), ytop, ybot
        s.studs = frozenset(cells) if studs else frozenset()

    def line(s):
        return f"1 {s.color} {fmt(s.x)} {fmt(s.y)} {fmt(s.z)} {ROT[s.rot]} {s.name}.dat"


def fmt(v):
    v = round(v, 3)
    return str(int(v)) if v == int(v) else str(v)


parts = []


def rect(i0, k0, nx, nz): return [(i, k) for i in range(i0, i0 + nx) for k in range(k0, k0 + nz)]


def place(sub, name, color, cells, ytop, h, studs=True, rot=None, y=None):
    """Teil ueber Zellen (Ursprung oben, Mitte der Grundflaeche). rot None: lange Seite bestimmt die Drehung."""
    xs = [c[0] for c in cells]; zs = [c[1] for c in cells]
    nx, nz = max(xs) - min(xs) + 1, max(zs) - min(zs) + 1
    if rot is None: rot = 90 if nz > nx else 0
    x = (min(xs) + max(xs) + 1) / 2 * LDU; z = (min(zs) + max(zs) + 1) / 2 * LDU
    p = Part(sub, name, color, x, ytop if y is None else y, z, rot, cells, ytop, ytop + h, studs)
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


# ================= Grundriss =================
# Zellen i (x) und k (z) von -16..15. Hinten = -z (Wand), vorne = +z (Betrachter). Von vorne gesehen liegt +x LINKS.
ALL = rect(-16, -16, 32, 32)
BACK = set(rect(-16, -16, 32, 2))                    # Rueckwand, 2 tief
SIDE = set(rect(-16, -14, 2, 12))                    # Seitenwand (von vorne rechts), k -14..-3
DADO = set(rect(-14, -14, 30, 2))                    # Sockel vor der Rueckwand
FRAME_I = (-12, 11)                                  # Rahmen aussen, 24 breit
PAINT_I = (-10, 9)                                   # Bildflaeche 20 breit
PW = PAINT_I[1] - PAINT_I[0] + 1
WALL_G = 20                                          # Wandhoehe in Steinen (480 LDU)
DADO_G = 3
Y_WALL, Y_DADO = -WALL_G * BH, -DADO_G * BH
Y_LIP_BOT = Y_DADO - PH                              # Oberkante untere Rahmenleiste (-80)
ROWS = 48                                            # Bildzeilen (Platten) zwischen den Goldleisten (Vielfaches von 3)
Y_PAINT_TOP = Y_LIP_BOT - PH - ROWS * PH             # Oberkante Bild (-472)
Y_FRAME_TOP = Y_PAINT_TOP - PH                       # Oberkante obere Innenleiste (-400)

# ---- Grundplatte ----
parts.append(Part("boden", "3811", BLACK, 0, 0, 0, 0, ALL, 0, 4))

# ---- Rueckwand + Seitenwand (Verband: Laeufer 2x4, Ecke wechselt je Lage) ----
for g in range(WALL_G):
    yt = -(g + 1) * BH
    if g % 2 == 0:                                   # Rueckwand laeuft durch die Ecke
        runs_b = [(i, 4) for i in range(-16, 16, 4)]
        runs_s = [(-14, 4), (-10, 4), (-6, 4)]
    else:                                            # Seitenwand laeuft durch die Ecke
        runs_b = [(-14, 2)] + [(i, 4) for i in range(-12, 16, 4)]
        runs_s = [(-16, 4), (-12, 4), (-8, 4), (-4, 2)]
    for i0, n in runs_b: place("wand", BRICK[(2, n)], RED, rect(i0, -16, n, 2), yt, BH)
    for k0, n in runs_s: place("wand", BRICK[(2, n)], RED, rect(-16, k0, 2, n), yt, BH)
# Wandkrone: vorne Gold, hinten Rot
pack("wand", [c for c in rect(-14, -15, 30, 1)] , GOLD, Y_WALL - PH, TILE, PH, studs=False)
pack("wand", [c for c in rect(-16, -16, 32, 1)], RED, Y_WALL - PH, TILE, PH, studs=False)
pack("wand", [(-15, k) for k in range(-15, -2)], GOLD, Y_WALL - PH, TILE, PH, studs=False)
pack("wand", [(-16, k) for k in range(-15, -2)], RED, Y_WALL - PH, TILE, PH, studs=False)

# ---- Sockel (Dunkelrot, 3 Steine) mit Goldleiste ausserhalb des Rahmens ----
for g in range(DADO_G):
    yt = -(g + 1) * BH
    starts = list(range(-14, 16, 4)) if g % 2 == 0 else [-14] + list(range(-12, 16, 4))
    for n_i, i0 in enumerate(starts):
        n = 2 if (g % 2 == 1 and i0 == -14) else min(4, 16 - i0)
        place("wand", BRICK[(2, n)], DKRED, rect(i0, -14, n, 2), yt, BH)
cap = [c for c in DADO if not FRAME_I[0] <= c[0] <= FRAME_I[1]]
pack("wand", cap, GOLD, Y_DADO - PH, TILE, PH, studs=False)

# ================= Goldrahmen =================
# untere Leiste 2 tief auf dem Sockel
NCOL = (ROWS * PH + PH) // BH                        # Steine je Rahmensaeule (+1 Platte)
for i0 in range(FRAME_I[0], FRAME_I[1] + 1, 8):
    place("rahmen", PLATE[(2, 8)], GOLD, rect(i0, -14, 8, 2), Y_LIP_BOT, PH)
# aeussere Saeulen (2 tief) von der Leiste bis zur Oberkante: 1 Platte + 13 Steine
for i in FRAME_I:
    place("rahmen", PLATE[(1, 2)], GOLD, rect(i, -14, 1, 2), Y_LIP_BOT - PH, PH)
    for g in range(NCOL):
        place("rahmen", BRICK[(1, 2)], GOLD, rect(i, -14, 1, 2), Y_LIP_BOT - PH - (g + 1) * BH, BH)
# innere Stufe (nur hintere Ebene k=-14): Spalten i=-9 und 8, Zeile unten und oben
for i in (FRAME_I[0] + 1, FRAME_I[1] - 1):
    place("rahmen", PLATE[(1, 1)], GOLD, [(i, -14)], Y_LIP_BOT - PH, PH)
    for g in range(NCOL):
        place("rahmen", BRICK[(1, 1)], GOLD, [(i, -14)], Y_LIP_BOT - PH - (g + 1) * BH, BH)
pack("rahmen", rect(PAINT_I[0], -14, PW, 1), GOLD, Y_LIP_BOT - PH, PLATE, PH)
pack("rahmen", rect(PAINT_I[0], -14, PW, 1), GOLD, Y_FRAME_TOP, PLATE, PH)
# obere Leiste 3 tief (liegt auf Rahmen und Wandkrone ist hoeher -> nur Rahmen), mit Goldfliesen
Y_LIP_TOP = Y_FRAME_TOP - PH
for i0 in range(FRAME_I[0], FRAME_I[1] + 1, 8):
    place("rahmen", PLATE[(2, 8)], GOLD, rect(i0, -14, 8, 2), Y_LIP_TOP, PH)
pack("rahmen", rect(FRAME_I[0], -14, FRAME_I[1] - FRAME_I[0] + 1, 2), GOLD, Y_LIP_TOP - PH, TILE, PH, studs=False)

# ================= Gemaelde (Pixelbild) =================
PAL_PAINT = [0, 15, 3, 288, 4, 320, 78, 92, 84, 70, 72, 71, 297, 191, 19, 28, 308]


def raster_painting(cover):
    sys.path.insert(0, os.path.join(HERE, "..", "tools", "relief"))
    import make_relief as mr
    from PIL import Image
    im = Image.open(cover).convert("RGB")
    s = im.size[0] / 250
    im = im.crop((int(79 * s), int(79 * s), int(171 * s), int(171 * s))).resize((PW, ROWS), Image.LANCZOS)
    allp = {**mr.PALETTE, **mr.EXTRA}
    pal = {c: allp[c] for c in PAL_PAINT if c in allp}
    lab = {c: mr.srgb_to_lab(v[2]) for c, v in pal.items()}
    rows = []
    for r in range(ROWS):
        L = []
        for c in range(PW):
            px = im.getpixel((c, r)); q = mr.srgb_to_lab(px)
            if px[1] > px[0] + 35 and px[2] > px[0] + 15:          # tuerkiser Hintergrund des Gemaeldes
                L.append(3 if sum(px) > 165 else 288); continue
            L.append(min(lab, key=lambda k: sum((u - v) ** 2 for u, v in zip(q, lab[k]))))
        rows.append(L)
    return rows, {c: [pal[c][0], pal[c][1]] for c in set(x for r in rows for x in r)}


GJ = os.path.join(HERE, "gemaelde.json")
if len(sys.argv) > 1:
    pix, pcols = raster_painting(sys.argv[1])
    json.dump({"hinweis": "Ballerina-Gemaelde, 20 x 48 (Zeile 0 = oben, Spalte 0 = links), LDraw-Farben",
               "pixel": pix, "farben": pcols}, open(GJ, "w"), indent=0)
G = json.load(open(GJ))
pix = G["pixel"]
for c, (nm, bl) in G["farben"].items(): COLORS.setdefault(int(c), (nm, bl))

# Bildzeile r (0 oben) -> Plattenlage; Spalte c (0 links) -> i = 7 - c (von vorne liegt +x links)
for r in range(ROWS):
    yt = Y_PAINT_TOP + r * PH
    cells = {(PAINT_I[1] - c, -14): pix[r][c] for c in range(PW)}
    # waagerecht zusammenfassen (1x2..1x4) fuer Verbund; ungerade Zeilen beginnen mit 1x1 (Versatz)
    c = 0
    while c < PW:
        n = 1
        while n < 4 and c + n < PW and pix[r][c + n] == pix[r][c] and not (r % 2 and c == 0):
            n += 1
        rc = [(PAINT_I[1] - c - j, -14) for j in range(n)]
        place("gemaelde", PLATE[(1, n)], pix[r][c], rc, yt, PH); c += n


# ================= Boden: Schachbrett =================
FLOOR = set(ALL) - BACK - SIDE - DADO
PODEST_C = (0.0, -6.0)                               # Mitte (Gitterpunkt), in Zellen


def in_podest(c): return math.hypot(c[0] + 0.5 - PODEST_C[0], c[1] + 0.5 - PODEST_C[1]) <= 4.3


PODEST = {c for c in FLOOR if in_podest(c)}
TABLE = rect(-14, 1, 6, 2)
LEGS = [(-14, 1), (-9, 1), (-14, 2), (-9, 2)]
CHAIRS = [-13, -10]
CHAIR_CELLS = {(i, k) for i in CHAIRS for k in (-1, 0)}
PLAQUE = rect(-2, 15, 4, 1)
BORDER = {c for c in FLOOR if c[1] == 15}
floor_tiles = FLOOR - PODEST - set(LEGS) - CHAIR_CELLS - {(13, -12), (-14, -12)}


def checker(c):
    if c in BORDER: return GOLD if c in PLAQUE else BLACK
    return BLACK if ((c[0] // 2) + (c[1] // 2)) % 2 == 0 else WHITE


# 2x2-Bloecke im Raster, Reste als 1x1/1x2
rest = set(floor_tiles)
for c in sorted(floor_tiles):
    if c[0] % 2 == 0 and c[1] % 2 == 0:
        blk = rect(c[0], c[1], 2, 2)
        if all(q in rest and q not in BORDER for q in blk):
            place("boden", TILE[(2, 2)], checker(c), blk, -PH, PH, studs=False); rest -= set(blk)
pack("boden", rest, None, -PH, {k: v for k, v in TILE.items() if k[0] == 1}, PH, studs=False, colfn=checker)

# ================= Podest =================
pack("podest", PODEST, BLACK, -PH, PLATE, PH, prefer_x=True)
pack("podest", PODEST, DKTURQ, -2 * PH, PLATE, PH, prefer_x=False)
FEET = [(-1, -6), (0, -6)]
pack("podest", PODEST - set(FEET), DKTURQ, -3 * PH, TILE, PH, studs=False)

# ================= Ballerina =================
y = -2 * PH                                          # Oberkante Podest-Platten (-16)
for f in FEET: place("ballerina", "6141", WHITE, [f], y - PH, PH)            # Spitzenschuhe
y -= PH
for g in range(4):                                   # Beine (Strumpfhose)
    for f in FEET: place("ballerina", "3062b", LNOUGAT, [f], y - BH, BH)
    y -= BH
TORSO = rect(-1, -7, 2, 2)
place("ballerina", "11213", BLACK, rect(-3, -9, 6, 6), y - PH, PH); y -= PH  # Tutu unten 6x6
place("ballerina", "60474", BLACK, rect(-2, -8, 4, 4), y - PH, PH); y -= PH  # Tutu oben 4x4
for g in range(2):                                   # Trikot
    place("ballerina", "3941", BLACK, TORSO, y - BH, BH); y -= BH
place("ballerina", PLATE[(1, 6)], LNOUGAT, rect(-3, -6, 6, 1), y - PH, PH)   # Arme (zweite Position)
place("ballerina", PLATE[(1, 2)], BLACK, rect(-1, -7, 2, 1), y - PH, PH)     # Ruecken
y -= PH
# Weinglas in der Hand (von vorne links = +x), Hand rechts leer
GI = (2, -6)
place("ballerina", "6141", TCLEAR, [GI], y - PH, PH)
place("ballerina", "6141", TCLEAR, [GI], y - 2 * PH, PH)
place("ballerina", "3062b", TRED, [GI], y - 2 * PH - BH, BH)
place("ballerina", "4032a", LNOUGAT, TORSO, y - PH, PH); y -= PH             # Schultern/Hals
place("ballerina", "4032a", LNOUGAT, TORSO, y - PH, PH); y -= PH            # Kinn
place("ballerina", "4032a", BLACK, TORSO, y - PH, PH); y -= PH               # Maske (Augen)
place("ballerina", "4032a", LNOUGAT, TORSO, y - PH, PH); y -= PH            # Stirn
place("ballerina", "30367b", BLACK, TORSO, y - BH, BH); y -= BH             # Haar (Kuppel)
p = place("ballerina", "15470", BLACK, TORSO, y - 18, 18, studs=False, y=y)  # Dutt (Ursprung unten)

# ================= Standleuchter links und rechts vom Bild =================
CANDLES = [(13, -12), (-14, -12)]
for c in CANDLES:
    place("tafel", "6141", GOLD, [c], -PH, PH)
    for g in range(6): place("tafel", "3062b", GOLD, [c], -PH - (g + 1) * BH, BH)
    yc = -PH - 6 * BH
    place("tafel", "6141", WHITE, [c], yc - PH, PH)
    place("tafel", "15470", TYELLOW, [c], yc - PH - 18, 18, studs=False, y=yc - PH)

# ================= Runaway-Dinnertafel =================
for c in LEGS:
    for g in range(3): place("tafel", "3062b", WHITE, [c], -(g + 1) * BH, BH)
place("tafel", PLATE[(2, 6)], WHITE, TABLE, -3 * BH - PH, PH)
YT = -3 * BH - PH
ITEMS = {(-13, 1): "teller", (-10, 1): "teller", (-12, 1): "leuchter", (-13, 2): "glas", (-10, 2): "glas",
         (-11, 2): "flasche"}
for c, what in ITEMS.items():
    if what == "teller": place("tafel", "98138", SILVER, [c], YT - PH, PH, studs=False)
    elif what == "glas":
        place("tafel", "6141", TCLEAR, [c], YT - PH, PH); place("tafel", "3062b", TRED, [c], YT - PH - BH, BH)
    elif what == "flasche":
        place("tafel", "3062b", DKGREEN, [c], YT - BH, BH); place("tafel", "6141", DKGREEN, [c], YT - BH - PH, PH)
        place("tafel", "4589", DKGREEN, [c], YT - 2 * BH - PH, BH, studs=False)
    elif what == "leuchter":
        place("tafel", "3062b", GOLD, [c], YT - BH, BH); place("tafel", "3062b", GOLD, [c], YT - 2 * BH, BH)
        place("tafel", "6141", WHITE, [c], YT - 2 * BH - PH, PH)
        place("tafel", "15470", TYELLOW, [c], YT - 2 * BH - PH - 18, 18, studs=False, y=YT - 2 * BH - PH)
pack("tafel", [c for c in TABLE if c not in ITEMS], WHITE, YT - PH, TILE, PH, studs=False)
for i in CHAIRS:                                     # Stuehle hinter der Tafel, Blick zum Betrachter
    place("tafel", PLATE[(1, 2)], BLACK, rect(i, -1, 1, 2), -PH, PH)
    place("tafel", "3005", BLACK, [(i, 0)], -PH - BH, BH)
    place("tafel", "3070b", DKRED, [(i, 0)], -PH - BH - PH, PH, studs=False)
    for g in range(2): place("tafel", "3005", BLACK, [(i, -1)], -PH - (g + 1) * BH, BH)
    place("tafel", "3070b", GOLD, [(i, -1)], -PH - 2 * BH - PH, PH, studs=False)


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
    loose = [n for n in range(len(parts)) if n not in seen]
    floating = [n for n in range(1, len(parts)) if not below[n]]
    occ = {}; coll = []
    for n, p in enumerate(parts[1:], 1):
        hit = False
        for c in p.cells:
            for yy in range(int(p.ytop), int(p.ybot), 2):
                if (c, yy) in occ and not hit: coll.append((occ[(c, yy)], n)); hit = True
                occ[(c, yy)] = n
    print("Teile:", len(parts), "| lose:", len(loose), "| schwebend:", len(floating), "| Kollisionen:", len(coll))
    for n in (loose + floating)[:10]:
        p = parts[n]; print("  !", p.sub, p.name, p.color, p.x, p.y, p.z)
    for a, b in coll[:10]:
        print("  X", parts[a].sub, parts[a].name, parts[a].ytop, sorted(parts[a].cells)[:2], "<->", parts[b].sub, parts[b].name, parts[b].ytop)
    return len(loose) + len(floating) + len(coll)


def export():
    order = [s for s in TITLES if any(p.sub == s for p in parts)]
    out = [f"0 FILE {NAME}.ldr", "0 Kanye West - My Beautiful Dark Twisted Fantasy - Diorama The Ballerina Room",
           f"0 Name: {NAME}.ldr", "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""]
    for s in order: out += [f"0 // {TITLES[s]}", f"1 16 0 0 0 {ROT[0]} {s}.ldr"]
    out += ["0 NOFILE"]
    for s in order:
        out += [f"0 FILE {s}.ldr", f"0 {TITLES[s]}", f"0 Name: {s}.ldr"] + [p.line() for p in parts if p.sub == s] + ["0 NOFILE"]
    open(os.path.join(OUT, f"{NAME}.mpd"), "w").write("\n".join(out) + "\n")
    bom = Counter((p.name, p.color) for p in parts)
    rows = ["LDraw Part,BrickLink ID,Farbe,Menge"]; xml = ["<INVENTORY>"]
    for (nm, c), q in sorted(bom.items()):
        bl = BL_ID.get(nm, nm); cn, blc = COLORS[c]
        rows.append(f"{nm}.dat,{bl},{cn},{q}")
        xml.append(f"<ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID><COLOR>{blc}</COLOR><MINQTY>{q}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    open(os.path.join(OUT, f"{NAME}_bom.csv"), "w").write("\n".join(rows) + "\n")
    open(os.path.join(OUT, f"{NAME}_bricklink.xml"), "w").write("\n".join(xml) + "\n")
    print("Teile gesamt:", sum(bom.values()), "| Positionen:", len(bom))
    for s in order: print(f"  {s}: {sum(1 for p in parts if p.sub == s)}")


bad = checks()
export()
print("CHECK", "OK" if bad == 0 else f"FEHLER ({bad})")
