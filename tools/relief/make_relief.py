"""
Relief-Mosaik ("Chaos-Pixel-Art") aus einem Bild – Stil wie die Wandbilder von mbrick_art:
Jede Zelle ist ein Stapel (Steine/Platten) mit einem zufaelligen Abschlussteil (Rundstein, Kegel, Rundplatte,
Fliese, Technic-Stein, Gitter, Cheese-Slope, Bluete, Schuessel ...). Farben kommen aus dem Bild, Hoehen aus einer
Hoehenkarte: Hintergrund flach mit Wolken-Relief, Motive treten als Kuppeln oder Plateaus heraus. Ueber eine
Zonen-Datei (JSON) bekommen einzelne Bildteile eigene Hoehen, Teile-Pools und Spezialteile (z. B. Satelliten-
schuesseln entlang eines Rings).

Aufruf:
  python3 make_relief.py bild.jpg ausgabe/name [--breite 48] [--hoehe 48] [--seed 1] [--chaos 0.35] [--tiefe 2]
                          [--konfetti 0.05] [--wolken 3] [--zonen zonen.json] [--farben 0,15,71,72,...]

Zonen-Datei: Liste von Objekten, Koordinaten als Bruchteil der Bildbreite/-hoehe (0..1):
  {"name": "...", "form": "ellipse" | "ring" | "rechteck" | "rahmen" | "punkt",
   "mitte": [u, v], "radius": [ru, rv], "breite": w (nur ring), "von": [u, v], "bis": [u, v] (rechteck),
   "hoehe": Platten ueber Grund, "profil": "flach" | "kuppel",
   "teile": ["4589", "3069b", ...]  (bevorzugte Abschlussteile je Groesse 1x1/1x2/2x2), "farbe_rgb": [r,g,b], "toleranz": 80 (nur passende Pixel),
   "sauber": true (Bildfarbe ohne Chaos/Konfetti), "licht": false | "schatten", "glatt": true (exakte Hoehe), "striche": "x" | "z" (Pinselstriche aus 1x2-1x4-Teilen), "kontur": true (Umriss aus
   Slopes), "teil": "85861" (handgesetztes Detail, genau dieses Teil, keine Zusammenfassung),
   "mischung": {"4": 0.7, "320": 0.3} (Farbmix), "zweifarbig": [0, 15] + "schwelle": 50 (Helligkeit L*),
   "spezial": {"teil": "4740", "abstand": 4, "farbe": 15, "extra": 1}  (Spezialteile verteilt)}
Spaetere Zonen ueberschreiben fruehere.

Ausgabe: name.mpd (Relief auf Grundplatte, Noppen nach oben = zum Betrachter, Bild oben = -z, Bild links = +x; per
Render geprueft: nicht gespiegelt), name_bom.csv, name_bricklink.xml, name_vorschau.png (Farben), name_hoehen.png.
"""
import argparse, json, math, os, random
from collections import Counter
from PIL import Image

LDU, BH, PH = 20, 24, 8

# LDraw-Farbe: (Name, BrickLink-ID, RGB)
PALETTE = {
    0: ("Black", 11, (27, 42, 52)), 15: ("White", 1, (244, 244, 244)), 71: ("Light Bluish Gray", 86, (160, 165, 169)),
    72: ("Dark Bluish Gray", 85, (108, 110, 104)), 1: ("Blue", 7, (0, 85, 191)), 4: ("Red", 5, (201, 26, 9)),
    14: ("Yellow", 3, (242, 205, 55)), 2: ("Green", 6, (35, 120, 65)), 19: ("Tan", 2, (228, 205, 158)),
    28: ("Dark Tan", 69, (149, 138, 115)), 70: ("Reddish Brown", 88, (88, 42, 18)), 25: ("Orange", 4, (254, 138, 24)),
    191: ("Bright Light Orange", 110, (248, 187, 61)), 320: ("Dark Red", 59, (114, 14, 15)),
    272: ("Dark Blue", 63, (10, 52, 99)), 288: ("Dark Green", 80, (24, 70, 50)), 73: ("Medium Blue", 42, (90, 147, 219)),
    322: ("Medium Azure", 156, (54, 174, 191)), 27: ("Lime", 34, (187, 233, 11)), 26: ("Magenta", 71, (144, 31, 118)),
    30: ("Medium Lavender", 157, (160, 110, 185)), 84: ("Medium Nougat", 150, (170, 125, 85)),
    308: ("Dark Brown", 120, (53, 33, 0)), 85: ("Dark Purple", 89, (63, 54, 145)),
    29: ("Bright Pink", 104, (228, 173, 200)), 5: ("Dark Pink", 47, (200, 112, 160)), 31: ("Lavender", 154, (205, 164, 222)),
    353: ("Coral", 220, (255, 109, 119)), 379: ("Sand Blue", 55, (112, 129, 154)), 226: ("Bright Light Yellow", 103, (255, 240, 58)),
}
# Zusatzfarben: nur aktiv mit --farben-plus (die Standardpalette bleibt gleich, alte Reliefs bleiben reproduzierbar)
EXTRA = {3: ("Dark Turquoise", 39, (6, 157, 159)), 151: ("Sand Green", 48, (160, 188, 172)),
         92: ("Nougat", 28, (208, 145, 104)), 78: ("Light Nougat", 90, (246, 215, 179)),
         297: ("Pearl Gold", 115, (170, 127, 46)), 179: ("Flat Silver", 95, (137, 135, 136)), 47: ("Trans-Clear", 12, (238, 238, 238)), 36: ("Trans-Red", 17, (201, 26, 9))}
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "3062b": "3062", "6141": "4073", "4032a": "4032"}

# Abschlussteile: Name -> (Hoehe in LDU ueber der Auflage, Ursprung unten?, Gewicht)
TOP_1x1 = {"3062b": (24, False, 5), "6141": (8, False, 4), "85861": (8, False, 3), "4589": (24, False, 4),
           "3070b": (8, False, 2), "98138": (8, False, 3), "3024": (8, False, 2), "3005": (24, False, 2),
           "54200": (16, True, 3), "35464": (16, True, 2), "33291": (8, False, 2), "24866": (8, False, 1),
           "15470": (18, True, 1), "4070": (24, False, 1), "11610": (32, False, 1), "2555": (8, False, 1),
           "25269": (8, False, 1), "24246": (8, False, 1)}
TOP_1x2 = {"3004": (24, False, 3), "3023": (8, False, 2), "3069b": (8, False, 2), "2412b": (8, False, 2),
           "85984": (16, True, 2), "3700": (24, False, 2), "32000": (24, False, 1), "3794b": (8, False, 1)}
TOP_2x2 = {"3941": (24, False, 3), "92947": (24, False, 2), "98100": (24, False, 2), "4740": (8, False, 2),
           "4032a": (8, False, 1), "18674": (8, False, 1), "4150": (8, False, 1), "98262": (24, False, 1),
           "15068": (16, True, 1), "3942c": (48, False, 1)}
SPECIAL = {"33061": (1, 48), "2343": (1, 40), "4740": (2, 8), "3960": (4, 16), "43898": (3, 16), "98262": (2, 24), "3942c": (2, 48), "3068b": (2, 8),
           "92947": (2, 24), "4150": (2, 8), "60474": (4, 8), "14769": (2, 8), "98100": (2, 24)}   # (Groesse, Hoehe)
# Pinselstriche: lange, schmale Teile in Strichrichtung (Laenge -> Teile); Hoehe, Ursprung unten?, Gewicht
TOP_LONG = {2: {"3069b": (8, False, 3), "3023": (8, False, 2), "35480": (8, False, 2), "85984": (16, True, 1)},
            3: {"63864": (8, False, 3), "3623": (8, False, 2)},
            4: {"2431": (8, False, 3), "3710": (8, False, 2)}}
SLOPED = {"54200", "35464", "85984", "15068", "15470"}          # Teile mit Gefaelle-Richtung (Formfolge)
ALL_TOPS = {**TOP_1x1, **TOP_1x2, **TOP_2x2, **{n: v for t in TOP_LONG.values() for n, v in t.items()}}
ROT = {0: "1 0 0 0 1 0 0 0 1", 90: "0 0 -1 0 1 0 1 0 0", 180: "-1 0 0 0 1 0 0 0 -1", 270: "0 0 1 0 1 0 -1 0 0"}


def srgb_to_lab(rgb):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(float(v)) for v in rgb)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    return (116 * t(Y) - 16, 500 * (t(X) - t(Y)), 200 * (t(Y) - t(Z)))


def fmt(v):
    v = round(v, 3)
    return str(int(v)) if v == int(v) else str(v)


def vnoise(x, z, sc, seed):
    def h(i, k): return (math.sin(i * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453) % 1.0
    x, z = x / sc, z / sc; i, k = math.floor(x), math.floor(z); fx, fz = x - i, z - k
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = h(i, k) + (h(i + 1, k) - h(i, k)) * sx; b = h(i, k + 1) + (h(i + 1, k + 1) - h(i, k + 1)) * sx
    return a + (b - a) * sz


def zone_weight(z, i, k, W, H):
    """0..1 Zugehoerigkeit der Zelle (i, k) zur Zone (1 = Kern), None = ausserhalb"""
    u, v = (i + 0.5) / W, (k + 0.5) / H
    f = z["form"]
    if f == "rechteck":
        (u0, v0), (u1, v1) = z["von"], z["bis"]
        return 1.0 if u0 <= u <= u1 and v0 <= v <= v1 else None
    if f == "bitmap":                                           # Pixel-Motiv: Zeichen je Noppe, "." = frei
        i0, k0 = z["ursprung"]; px = z["pixel"]
        r, c = k - k0, i - i0
        return 1.0 if 0 <= r < len(px) and 0 <= c < len(px[r]) and px[r][c] != "." else None
    if f == "rahmen":                                           # Rechteck-Umriss mit Breite "breite"
        (u0, v0), (u1, v1) = z["von"], z["bis"]; b = z.get("breite", 0.02)
        inside = u0 <= u <= u1 and v0 <= v <= v1
        inner = u0 + b <= u <= u1 - b and v0 + b <= v <= v1 - b
        return 1.0 if inside and not inner else None
    (mu, mv), (ru, rv) = z["mitte"], z.get("radius", [0.02, 0.02])
    d = math.hypot((u - mu) / ru, (v - mv) / rv)
    if f in ("ellipse", "punkt"):
        return 1.0 - d if d <= 1.0 else None
    if f == "ring":
        w = z.get("breite", 0.02) / max(ru, rv)
        return 1.0 - abs(d - 1.0) / w if abs(d - 1.0) <= w else None
    raise ValueError(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bild"); ap.add_argument("ausgabe")
    ap.add_argument("--breite", type=int, default=48); ap.add_argument("--hoehe", type=int, default=48)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--chaos", type=float, default=0.35, help="Anteil Zellen mit Nachbarfarbe (Farbmix)")
    ap.add_argument("--tiefe", type=int, default=2, help="zufaellige Zusatz-Platten pro Zelle (Rauschen)")
    ap.add_argument("--wolken", type=int, default=0, help="Hintergrund-Relief: helle Stellen bis zu N Platten hoeher")
    ap.add_argument("--farben", default="", help="LDraw-Farbcodes kommagetrennt (Standard: ganze Palette)")
    ap.add_argument("--konfetti", type=float, default=0.05, help="Anteil bunter Akzentfarben gleicher Helligkeit")
    ap.add_argument("--zonen", default="", help="JSON-Datei mit Zonen (Hoehen, Teile, Spezialteile)")
    ap.add_argument("--licht", type=float, default=0.0,
                    help="Licht und Schatten wie ein Maler (0 = aus, 1 = normal): Licht von links oben, beleuchtete "
                         "Flaechen eine Stufe heller, abgewandte eine Stufe dunkler (gleicher Farbton)")
    ap.add_argument("--formfolge", action="store_true", help="Slopes zeigen der Form nach (Gefaelle der Hoehenkarte)")
    ap.add_argument("--farben-plus", default="", help="Zusatzfarben aktivieren, z. B. 3,151,92,78,297 (siehe EXTRA)")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    W, H = a.breite, a.hoehe
    PALETTE.update(EXTRA)
    plus = {int(c) for c in a.farben_plus.split(",") if c}
    pal = {c: v for c, v in PALETTE.items() if (c not in EXTRA or c in plus) and (not a.farben or str(c) in a.farben.split(","))}
    lab = {c: srgb_to_lab(v[2]) for c, v in pal.items()}
    zones = json.load(open(a.zonen)) if a.zonen else []

    img = Image.open(a.bild).convert("RGB")
    s = min(img.width / W, img.height / H)
    cw, ch = W * s, H * s
    img = img.crop(((img.width - cw) / 2, (img.height - ch) / 2, (img.width + cw) / 2, (img.height + ch) / 2))
    small = img.resize((W, H), Image.LANCZOS)

    # ---- Farben ----
    col, rgb, lum = {}, {}, {}
    for k in range(H):
        for i in range(W):
            px = small.getpixel((i, k)); L = srgb_to_lab(px)
            d = sorted((sum((p - q) ** 2 for p, q in zip(L, lab[c])), c) for c in pal)
            c = d[0][1]
            if len(d) > 1 and d[1][0] < d[0][0] * 1.9 + 60 and rng.random() < a.chaos: c = d[1][1]
            if rng.random() < a.konfetti:
                acc = [cc for cc in pal if abs(lab[cc][0] - L[0]) < 16 and math.hypot(lab[cc][1], lab[cc][2]) > 25]
                if acc: c = rng.choice(acc)
            if c in (47, 36): c = d[0][1] if d[0][1] not in (47, 36) else 4          # Trans-Farben nur gezielt
            col[(i, k)], rgb[(i, k)], lum[(i, k)] = c, px, L[0]

    # ---- Hoehenkarte (in Platten) ----
    lo, hi = min(lum.values()), max(lum.values())
    hgt, pool = {}, {}
    stroke, solo, lmode = {}, set(), {}
    for q in col:
        n = vnoise(q[0], q[1], 3.0, a.seed) * (a.tiefe + 1) * 0.8 + rng.random() * 1.2
        if a.wolken: n += a.wolken * vnoise(q[0], q[1], 5.0, a.seed + 7) * ((lum[q] - lo) / max(1, hi - lo)) * 1.4
        hgt[q] = min(a.tiefe + a.wolken, int(n))
    for z in zones:
        members = []
        for q in col:
            w = zone_weight(z, q[0], q[1], W, H)
            if w is None: continue
            if "farbe_rgb" in z and math.dist(rgb[q], z["farbe_rgb"]) > z.get("toleranz", 80): continue
            members.append(q)
            base = z.get("hoehe", 0)
            if z.get("profil") == "kuppel": base = base * math.sqrt(max(0.0, 1 - (1 - w) ** 2))
            if z.get("glatt"): hgt[q] = int(round(base))           # exakt (fuer Pinselstriche, Rahmenprofil)
            else: hgt[q] = max(hgt[q], int(round(base)) + rng.choice((0, 0, 1)))
            if z.get("teile"): pool[q] = z["teile"]
            if z.get("teil"): pool[q] = [z["teil"]]; solo.add(q)   # handgesetztes Detail: genau dieses Teil
            if z.get("striche"): stroke[q] = z["striche"]
            else: stroke.pop(q, None)
            if "licht" in z: lmode[q] = z["licht"]                  # false = keine Schattierung, "schatten" = nur dunkler
            else: lmode.pop(q, None)
            if z.get("sauber"):                                  # reine Bildfarbe, ohne Chaos/Konfetti (Motiv sauber halten)
                Lq = srgb_to_lab(rgb[q])
                col[q] = min((c for c in pal if c not in (47, 36)), key=lambda c: sum((u - v) ** 2 for u, v in zip(Lq, lab[c])))
            if "farbe" in z: col[q] = z["farbe"]
            if z["form"] == "bitmap":
                ch = z["pixel"][q[1] - z["ursprung"][1]][q[0] - z["ursprung"][0]]
                col[q] = z["farben"][ch]
                hgt[q] = z.get("hoehen", {}).get(ch, z.get("hoehe", 0))
                if ch in z.get("teile_je", {}): pool[q] = z["teile_je"][ch]
                lmode[q] = False
            if "mischung" in z:                                  # gewichteter Farbmix, z. B. Stoff aus Rot + Dunkelrot
                cs = [int(c) for c in z["mischung"]]
                col[q] = rng.choices(cs, weights=[z["mischung"][str(c)] for c in cs])[0]
            if "zweifarbig" in z:                                # Hell/Dunkel-Schwelle, z. B. Aufkleber mit Schrift
                dk, lt = z["zweifarbig"]
                col[q] = lt if lum[q] > z.get("schwelle", 50) else dk
        if z.get("kontur"):                                      # Umriss: Slopes, die (mit --formfolge) nach aussen fallen
            ms = set(members)
            for q in members:
                if any((q[0] + a_, q[1] + b_) not in ms for a_, b_ in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    pool[q] = z.get("kontur_teile", ["54200", "35464", "54200"]); stroke.pop(q, None)

    # ---- Geglaettete Hoehen und Gefaelle (fuer Licht und Formfolge) ----
    def smooth_grad():
        hs = {q: sum(hgt.get((q[0] + a_, q[1] + b_), hgt[q]) for a_ in (-1, 0, 1) for b_ in (-1, 0, 1)) / 9 for q in hgt}
        return {q: ((hs.get((q[0] + 1, q[1]), hs[q]) - hs.get((q[0] - 1, q[1]), hs[q])) / 2,
                    (hs.get((q[0], q[1] + 1), hs[q]) - hs.get((q[0], q[1] - 1), hs[q])) / 2) for q in hs}

    # ---- Licht und Schatten: gleicher Farbton, eine Stufe heller/dunkler ----
    n_licht = 0
    if a.licht > 0:
        solid = {c: v for c, v in pal.items() if c not in (47, 36)}

        def step(c, up):
            L0, a0, b0 = lab[c]; ch = math.hypot(a0, b0)
            best = None
            for cc in solid:
                if cc == c or cc in (0, 15): continue                # nie in reines Schwarz/Weiss kippen
                L1, a1, b1 = lab[cc]
                dL = (L1 - L0) if up else (L0 - L1)
                dab = math.hypot(a1 - a0, b1 - b0)
                if dL < 6 or dL > 40 or dab > max(22, 0.45 * ch): continue
                score = dL + 1.5 * dab
                if best is None or score < best[0]: best = (score, cc)
            return best[1] if best else None
        ramp = {c: (step(c, False), step(c, True)) for c in solid}
        grad = smooth_grad()
        Lv = (-1.0, -1.0, 1.2); Ln = math.sqrt(sum(v * v for v in Lv)); flat = Lv[2] / Ln
        for q, (gx, gz) in grad.items():
            nx, nz = -0.4 * gx, -0.4 * gz; nn = math.sqrt(nx * nx + nz * nz + 1)
            sh = (nx * Lv[0] + nz * Lv[1] + Lv[2]) / nn / Ln - flat
            c = col[q]; mode = lmode.get(q, True)
            if c not in ramp or mode is False or q in solo: continue
            # Dithering wie Pinselauftrag: Wahrscheinlichkeit waechst mit der Neigung zum/vom Licht
            p_up = max(0.0, min(1.0, (sh - 0.04) / 0.22)) * a.licht
            p_dn = max(0.0, min(1.0, (-sh - 0.04) / 0.22)) * a.licht
            u_ = rng.random()
            if mode != "schatten" and lab[c][0] > 25 and u_ < p_up and ramp[c][1] is not None:   # Schwarz bleibt schwarz
                col[q] = ramp[c][1]; n_licht += 1
            elif u_ < p_dn and ramp[c][0] is not None: col[q] = ramp[c][0]; n_licht += 1

    lines, bom = [], Counter()

    def put(name, c, x, y, z, rot=0):
        lines.append(f"1 {c} {fmt(x)} {fmt(y)} {fmt(z)} {ROT[rot]} {name}.dat"); bom[(name, c)] += 1

    def cx(i): return (W / 2 - i - 0.5) * LDU                   # von oben (Noppen zum Betrachter) liegt +x links
    def cz(k): return (k - H / 2 + 0.5) * LDU                   # Bildoberkante = -z

    def ctr(cells): return sum(cx(p[0]) for p in cells) / len(cells), sum(cz(p[1]) for p in cells) / len(cells)

    B, bp = (48, "4186") if W % 48 == 0 and H % 48 == 0 else (32, "3811") if W % 32 == 0 and H % 32 == 0 else (16, "91405")
    for bx in range(math.ceil(W / B)):
        for bz in range(math.ceil(H / B)):
            put(bp, 0, (bx * B + B / 2 - W / 2) * LDU, 0, (bz * B + B / 2 - H / 2) * LDU)

    done = set()

    def stack(q, n):
        """n Platten Hoehe: Steine 1x1 fuer je 3 Platten, Rest Platten (Farbe der Zelle)"""
        y = 0
        for _ in range(n // 3):
            put("3005", col[q], cx(q[0]), y - BH, cz(q[1])); y -= BH
        for _ in range(n % 3):
            put("3024", col[q], cx(q[0]), y - PH, cz(q[1])); y -= PH

    def pick(tab, prefer=None):
        if prefer:
            cand = [n for n in prefer if n in tab]
            if cand: return rng.choice(cand)
        names = list(tab); return rng.choices(names, weights=[tab[n][2] for n in names])[0]

    def top(name, c, x, surf, z, rot):
        h, bottom, _ = ALL_TOPS[name]
        put(name, c, x, surf if bottom else surf - h, z, rot)

    # ---- Spezialteile (z. B. Satellitenschuesseln entlang eines Rings) ----
    n_spec = 0
    for z in zones:
        sp = z.get("spezial")
        if not sp: continue
        size = SPECIAL[sp["teil"]][0]
        if z["form"] == "ring":
            (mu, mv), (ru, rv) = z["mitte"], z["radius"]
            pts = [((mu + ru * math.cos(2 * math.pi * t / 360)) * W, (mv + rv * math.sin(2 * math.pi * t / 360)) * H)
                   for t in range(360)]
        elif z["form"] == "punkt":
            pts = [(z["mitte"][0] * W, z["mitte"][1] * H)]
        else:
            cells = [q for q in col if zone_weight(z, q[0], q[1], W, H) is not None]
            rng.shuffle(cells); pts = [(q[0] + 0.5, q[1] + 0.5) for q in cells]
        placed = []
        for (px, pz) in pts:
            i0, k0 = int(round(px - size / 2)), int(round(pz - size / 2))
            fp = [(i0 + a_, k0 + b_) for a_ in range(size) for b_ in range(size)]
            if not all(q in col and q not in done for q in fp): continue
            if any(math.hypot(px - x_, pz - z_) < sp.get("abstand", size + 1) for x_, z_ in placed): continue
            n = max(hgt[q] for q in fp) + sp.get("extra", 0)
            c = sp.get("farbe", Counter(col[q] for q in fp).most_common(1)[0][0])
            for q in fp:
                hgt[q] = n; col[q] = c; stack(q, n)
            x, zz = ctr(fp)
            put(sp["teil"], c, x, -PH * n - SPECIAL[sp["teil"]][1], zz)
            done |= set(fp); placed.append((px, pz)); n_spec += 1

    # ---- Formfolge: Gefaelle je Zelle (Richtung im Raster, in der die Hoehe faellt) ----
    GRAD = smooth_grad() if a.formfolge else {}

    def fall_rot(cells, allowed=(0, 90, 180, 270)):
        """Rotation, bei der das Gefaelle eines Slopes zur tieferen Seite zeigt (None = eben)"""
        gx = sum(GRAD[p][0] for p in cells) / len(cells); gz = sum(GRAD[p][1] for p in cells) / len(cells)
        if math.hypot(gx, gz) < 0.25: return None
        # Gefaelle im Raster = -(gx, gz); Raster (di, dk) -> Welt (-di, dk); Slope-Standard faellt nach Welt -z (rot 0)
        want = {(1, 0): 90, (-1, 0): 270, (0, 1): 180, (0, -1): 0}
        dw = (gx, -gz)                                           # Welt-Richtung des Gefaelles (-(-gx), -gz)
        best = max(allowed, key=lambda r: dw[0] * {90: 1, 270: -1}.get(r, 0) + dw[1] * {180: 1, 0: -1}.get(r, 0))
        return best

    # ---- restliche Zellen ----
    for k in range(H):
        for i in range(W):
            q = (i, k)
            if q in done: continue
            c, n = col[q], hgt[q]
            if q in stroke:                                      # Pinselstrich: laengster passender Lauf in Strichrichtung
                dx, dz = (1, 0) if stroke[q] == "x" else (0, 1)
                run = [q]
                while len(run) < 4:
                    p_ = (run[-1][0] + dx, run[-1][1] + dz)
                    if p_ in col and p_ not in done and stroke.get(p_) == stroke[q] and col[p_] == c and hgt[p_] == n: run.append(p_)
                    else: break
                if len(run) >= 2:
                    L_ = rng.choice([m for m in (2, 3, 4) if m <= len(run)])
                    run = run[:L_]
                    for p_ in run: stack(p_, n)
                    nm = pick(TOP_LONG[L_])
                    rot = 0 if dx else 90
                    if nm in SLOPED and a.formfolge:
                        rr = fall_rot(run, (rot, rot + 180)); rot = rr if rr is not None else rot
                    x, zz = ctr(run)
                    top(nm, c, x, -PH * n, zz, rot % 360)
                    done |= set(run); continue
            r = rng.random() if q not in solo else 1.0
            quad = [(i, k), (i + 1, k), (i, k + 1), (i + 1, k + 1)]
            if r < 0.08 and all(p in col and p not in done and p not in solo and col[p] == c and hgt[p] == n for p in quad):
                for p in quad: stack(p, n)
                x, zz = ctr(quad)
                nm = pick(TOP_2x2, pool.get(q)); rot = 0
                if nm in SLOPED and a.formfolge: rot = fall_rot(quad) or 0
                top(nm, c, x, -PH * n, zz, rot)
                done |= set(quad); continue
            for pair, rot in (([(i, k), (i + 1, k)], 0), ([(i, k), (i, k + 1)], 90)):
                if r < 0.30 and all(p in col and p not in done and p not in solo and col[p] == c and hgt[p] == n for p in pair):
                    for p in pair: stack(p, n)
                    nm = pick(TOP_1x2, pool.get(q))
                    rr = rot + (180 if nm == "85984" and rng.random() < 0.5 else 0)
                    if nm in SLOPED and a.formfolge:
                        f_ = fall_rot(pair, (rot, rot + 180)); rr = f_ if f_ is not None else rr
                    x, zz = ctr(pair)
                    top(nm, c, x, -PH * n, zz, rr % 360)
                    done |= set(pair); break
            else:
                stack(q, n)
                nm = pick(TOP_1x1, pool.get(q))
                rot = rng.choice((0, 90, 180, 270))
                if nm in SLOPED and a.formfolge:
                    f_ = fall_rot([q]); rot = f_ if f_ is not None else rot
                top(nm, c, cx(i), -PH * n, cz(k), rot)
                done.add(q)
    assert len(done) == W * H

    name = os.path.basename(a.ausgabe)
    os.makedirs(os.path.dirname(a.ausgabe) or ".", exist_ok=True)
    out = [f"0 FILE {name}.ldr", f"0 Relief-Mosaik {name} ({W} x {H} Noppen)", f"0 Name: {name}.ldr",
           "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""] + lines + ["0 NOFILE"]
    open(a.ausgabe + ".mpd", "w").write("\n".join(out) + "\n")
    # BrickLink-Upload akzeptiert nur .ldr: dieselben Teile als einfache LDraw-Datei ohne FILE-Bloecke
    open(a.ausgabe + ".ldr", "w").write("\n".join([f"0 Relief-Mosaik {name} ({W} x {H} Noppen)", f"0 Name: {name}.ldr",
                                                   "0 Author: Claude Code (generiert)", ""] + lines) + "\n")
    rows = ["LDraw Part,BrickLink ID,Farbe,Menge"]; xml = ["<INVENTORY>"]
    for (nm, c), qn in sorted(bom.items()):
        bl = BL_ID.get(nm, nm)
        rows.append(f"{nm}.dat,{bl},{PALETTE[c][0]},{qn}")
        xml.append(f"<ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID><COLOR>{PALETTE[c][1]}</COLOR><MINQTY>{qn}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    open(a.ausgabe + "_bom.csv", "w").write("\n".join(rows) + "\n")
    open(a.ausgabe + "_bricklink.xml", "w").write("\n".join(xml) + "\n")
    prev = Image.new("RGB", (W, H)); hm = Image.new("L", (W, H))
    mh = max(hgt.values()) or 1
    for q, c in col.items():
        prev.putpixel(q, PALETTE[c][2]); hm.putpixel(q, int(255 * hgt[q] / mh))
    prev.resize((W * 10, H * 10), Image.NEAREST).save(a.ausgabe + "_vorschau.png")
    hm.resize((W * 10, H * 10), Image.NEAREST).save(a.ausgabe + "_hoehen.png")
    print(f"{W}x{H} Noppen | Teile {sum(bom.values())} | Positionen {len(bom)} | Teilesorten {len({n for n, _ in bom})} "
          f"| Farben {len({c for _, c in bom})} | Spezialteile {n_spec} | max. Hoehe {mh} Platten | Licht/Schatten {n_licht} Zellen")


if __name__ == "__main__":
    main()
