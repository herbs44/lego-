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
  {"name": "...", "form": "ellipse" | "ring" | "rechteck" | "punkt",
   "mitte": [u, v], "radius": [ru, rv], "breite": w (nur ring), "von": [u, v], "bis": [u, v] (rechteck),
   "hoehe": Platten ueber Grund, "profil": "flach" | "kuppel",
   "teile": ["4589", ...]  (bevorzugte 1x1-Abschlussteile), "farbe_rgb": [r,g,b], "toleranz": 80 (nur passende Pixel),
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
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "6141": "4073", "4032a": "4032"}

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
SPECIAL = {"4740": (2, 8), "3960": (4, 16), "43898": (3, 16), "98262": (2, 24), "3942c": (2, 48), "3068b": (2, 8),
           "92947": (2, 24), "4150": (2, 8), "60474": (4, 8), "14769": (2, 8), "98100": (2, 24)}   # (Groesse, Hoehe)
ALL_TOPS = {**TOP_1x1, **TOP_1x2, **TOP_2x2}
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
    a = ap.parse_args()
    rng = random.Random(a.seed)
    W, H = a.breite, a.hoehe
    pal = {c: v for c, v in PALETTE.items() if not a.farben or str(c) in a.farben.split(",")}
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
            col[(i, k)], rgb[(i, k)], lum[(i, k)] = c, px, L[0]

    # ---- Hoehenkarte (in Platten) ----
    lo, hi = min(lum.values()), max(lum.values())
    hgt, pool = {}, {}
    for q in col:
        n = vnoise(q[0], q[1], 3.0, a.seed) * (a.tiefe + 1) * 0.8 + rng.random() * 1.2
        if a.wolken: n += a.wolken * vnoise(q[0], q[1], 5.0, a.seed + 7) * ((lum[q] - lo) / max(1, hi - lo)) * 1.4
        hgt[q] = min(a.tiefe + a.wolken, int(n))
    for z in zones:
        for q in col:
            w = zone_weight(z, q[0], q[1], W, H)
            if w is None: continue
            if "farbe_rgb" in z and math.dist(rgb[q], z["farbe_rgb"]) > z.get("toleranz", 80): continue
            base = z.get("hoehe", 0)
            if z.get("profil") == "kuppel": base = base * math.sqrt(max(0.0, 1 - (1 - w) ** 2))
            hgt[q] = max(hgt[q], int(round(base)) + rng.choice((0, 0, 1)))
            if z.get("teile"): pool[q] = z["teile"]
            if "farbe" in z: col[q] = z["farbe"]

    lines, bom = [], Counter()

    def put(name, c, x, y, z, rot=0):
        lines.append(f"1 {c} {fmt(x)} {fmt(y)} {fmt(z)} {ROT[rot]} {name}.dat"); bom[(name, c)] += 1

    def cx(i): return (W / 2 - i - 0.5) * LDU                   # von oben (Noppen zum Betrachter) liegt +x links
    def cz(k): return (k - H / 2 + 0.5) * LDU                   # Bildoberkante = -z

    def ctr(cells): return sum(cx(p[0]) for p in cells) / len(cells), sum(cz(p[1]) for p in cells) / len(cells)

    B, bp = (48, "4186") if W % 48 == 0 and H % 48 == 0 else (32, "3811")
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

    # ---- restliche Zellen ----
    for k in range(H):
        for i in range(W):
            q = (i, k)
            if q in done: continue
            c, n = col[q], hgt[q]
            r = rng.random()
            quad = [(i, k), (i + 1, k), (i, k + 1), (i + 1, k + 1)]
            if r < 0.08 and all(p in col and p not in done and col[p] == c and hgt[p] == n for p in quad):
                for p in quad: stack(p, n)
                x, zz = ctr(quad)
                top(pick(TOP_2x2), c, x, -PH * n, zz, 0)
                done |= set(quad); continue
            for pair, rot in (([(i, k), (i + 1, k)], 0), ([(i, k), (i, k + 1)], 90)):
                if r < 0.30 and all(p in col and p not in done and col[p] == c and hgt[p] == n for p in pair):
                    for p in pair: stack(p, n)
                    nm = pick(TOP_1x2)
                    rr = rot + (180 if nm == "85984" and rng.random() < 0.5 else 0)
                    x, zz = ctr(pair)
                    top(nm, c, x, -PH * n, zz, rr % 360)
                    done |= set(pair); break
            else:
                stack(q, n)
                nm = pick(TOP_1x1, pool.get(q))
                top(nm, c, cx(i), -PH * n, cz(k), rng.choice((0, 90, 180, 270)))
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
          f"| Farben {len({c for _, c in bom})} | Spezialteile {n_spec} | max. Hoehe {mh} Platten")


if __name__ == "__main__":
    main()
