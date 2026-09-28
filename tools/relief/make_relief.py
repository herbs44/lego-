"""
Relief-Mosaik ("Chaos-Pixel-Art") aus einem Bild – Stil wie die Wandbilder von mbrick_art:
Jede Zelle ist ein Stapel aus 1x1-Platten mit einem zufaelligen Abschlussteil (Rundstein, Kegel, Rundplatte,
Fliese, Technic-Stein, Gitter, Cheese-Slope, Bluete ...). Farben kommen aus dem Bild, Hoehen und Teile variieren,
benachbarte gleichfarbige Zellen werden teils zu 1x2/2x2-Teilen zusammengefasst. Aus der Entfernung entsteht das
Bild, aus der Naehe eine lebendige Textur.

Aufruf:
  python3 make_relief.py bild.jpg ausgabe/name [--breite 48] [--hoehe 48] [--seed 1] [--chaos 0.35] [--tiefe 3]
                          [--konfetti 0.05] [--farben 0,15,71,72,...]

Ausgabe: name.mpd (Relief auf Grundplatte, Noppen nach oben = zum Betrachter, Bild oben = -z),
name_bom.csv, name_bricklink.xml, name_vorschau.png (flache Farbvorschau 1 Pixel = 1 Noppe, vergroessert).
"""
import argparse, math, os, random
from collections import Counter
from PIL import Image

LDU, BH, PH = 20, 24, 8

# LDraw-Farbe: (Name, BrickLink-ID, RGB) – haeufige, gut verfuegbare Farben
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
}
BL_ID = {"3070b": "3070", "3069b": "3069", "3068b": "3068", "6141": "4073", "3062b": "3062b", "4032a": "4032"}

# Abschlussteile: Name -> (Hoehe LDU, Ursprung unten?, Gewicht)
TOP_1x1 = {"3062b": (24, False, 5), "6141": (8, False, 5), "4589": (24, False, 3), "3070b": (8, False, 3),
           "98138": (8, False, 3), "3024": (8, False, 3), "3005": (24, False, 2), "54200": (16, True, 3),
           "33291": (8, False, 1), "15470": (18, True, 1), "4070": (24, False, 1)}
TOP_1x2 = {"3004": (24, False, 3), "3023": (8, False, 2), "3069b": (8, False, 2), "2412b": (8, False, 2),
           "85984": (16, True, 2), "3700": (24, False, 3), "3794b": (8, False, 1)}
TOP_2x2 = {"3941": (24, False, 3), "3003": (24, False, 1), "3068b": (8, False, 1), "4032a": (8, False, 2),
           "3022": (8, False, 1)}
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bild"); ap.add_argument("ausgabe")
    ap.add_argument("--breite", type=int, default=48); ap.add_argument("--hoehe", type=int, default=48)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--chaos", type=float, default=0.35, help="Anteil Zellen mit Nachbarfarbe (Farbmix wie im Original)")
    ap.add_argument("--tiefe", type=int, default=3, help="max. zusaetzliche Plattenlagen unter dem Abschlussteil")
    ap.add_argument("--farben", default="", help="LDraw-Farbcodes kommagetrennt (Standard: ganze Palette)")
    ap.add_argument("--konfetti", type=float, default=0.05,
                    help="Anteil Zellen mit bunter Akzentfarbe gleicher Helligkeit (Lila, Lime, Pink ... wie im Original)")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    W, H = a.breite, a.hoehe
    pal = {c: v for c, v in PALETTE.items() if not a.farben or str(c) in a.farben.split(",")}
    lab = {c: srgb_to_lab(v[2]) for c, v in pal.items()}

    img = Image.open(a.bild).convert("RGB")
    s = min(img.width / W, img.height / H)                      # zentrierter Zuschnitt aufs Seitenverhaeltnis
    cw, ch = W * s, H * s
    img = img.crop(((img.width - cw) / 2, (img.height - ch) / 2, (img.width + cw) / 2, (img.height + ch) / 2))
    small = img.resize((W, H), Image.LANCZOS)

    # Farbe je Zelle: naechste Palettenfarbe, mit 'chaos' die zweitnaechste, wenn sie fast genauso gut passt
    col, lum = {}, {}
    for k in range(H):
        for i in range(W):
            L = srgb_to_lab(small.getpixel((i, k)))
            d = sorted((sum((p - q) ** 2 for p, q in zip(L, lab[c])), c) for c in pal)
            c = d[0][1]
            if len(d) > 1 and d[1][0] < d[0][0] * 1.9 + 60 and rng.random() < a.chaos: c = d[1][1]
            if rng.random() < a.konfetti:                       # Konfetti: bunte Farbe mit aehnlicher Helligkeit
                acc = [cc for cc in pal if abs(lab[cc][0] - L[0]) < 16 and math.hypot(lab[cc][1], lab[cc][2]) > 25]
                if acc: c = rng.choice(acc)
            col[(i, k)], lum[(i, k)] = c, L[0]

    # Hoehe je Zelle (Plattenlagen): Cluster aus Rauschen + Zufall -> lebendige Tiefe
    hgt = {q: min(a.tiefe, int(vnoise(q[0], q[1], 3.0, a.seed) * (a.tiefe + 1) * 0.8 + rng.random() * 1.6))
           for q in col}

    lines, bom = [], Counter()

    def put(name, c, x, y, z, rot=0):
        lines.append(f"1 {c} {fmt(x)} {fmt(y)} {fmt(z)} {ROT[rot]} {name}.dat"); bom[(name, c)] += 1

    def cx(i): return (i - W / 2 + 0.5) * LDU
    def cz(k): return (k - H / 2 + 0.5) * LDU

    # Grundplatten (48x48), zentriert
    nb_x, nb_z = math.ceil(W / 48), math.ceil(H / 48)
    for bx in range(nb_x):
        for bz in range(nb_z):
            put("4186", 0, (bx * 48 + 24 - W / 2) * LDU, 0, (bz * 48 + 24 - H / 2) * LDU)

    done = set()

    def stack(q, n):
        for L in range(n):
            put("3024", col[q], cx(q[0]), -PH * (L + 1), cz(q[1]))

    def pick(tab):
        names = list(tab); return rng.choices(names, weights=[tab[n][2] for n in names])[0]

    def top(name, tab, c, x, surf, z, rot):
        h, bottom, _ = tab[name]
        put(name, c, x, surf if bottom else surf - h, z, rot)

    for k in range(H):
        for i in range(W):
            q = (i, k)
            if q in done: continue
            c, n = col[q], hgt[q]
            r = rng.random()
            quad = [(i, k), (i + 1, k), (i, k + 1), (i + 1, k + 1)]
            if r < 0.10 and all(p in col and p not in done and col[p] == c and hgt[p] == n for p in quad):
                for p in quad: stack(p, n)
                top(pick(TOP_2x2), TOP_2x2, c, cx(i) + LDU / 2, -PH * n, cz(k) + LDU / 2, 0)
                done |= set(quad); continue
            for pair, rot, ox, oz in (([(i, k), (i + 1, k)], 0, LDU / 2, 0), ([(i, k), (i, k + 1)], 90, 0, LDU / 2)):
                if r < 0.35 and all(p in col and p not in done and col[p] == c and hgt[p] == n for p in pair):
                    for p in pair: stack(p, n)
                    nm = pick(TOP_1x2)
                    rr = rot + (180 if nm == "85984" and rng.random() < 0.5 else 0)
                    top(nm, TOP_1x2, c, cx(i) + ox, -PH * n, cz(k) + oz, rr % 360)
                    done |= set(pair); break
            else:
                stack(q, n)
                nm = pick(TOP_1x1)
                top(nm, TOP_1x1, c, cx(i), -PH * n, cz(k), rng.choice((0, 90, 180, 270)))
                done.add(q)
    assert len(done) == W * H

    name = os.path.basename(a.ausgabe)
    os.makedirs(os.path.dirname(a.ausgabe) or ".", exist_ok=True)
    out = [f"0 FILE {name}.ldr", f"0 Relief-Mosaik {name} ({W} x {H} Noppen)", f"0 Name: {name}.ldr",
           "0 Author: Claude Code (generiert)", "0 !LDRAW_ORG Unofficial_Model", ""] + lines + ["0 NOFILE"]
    open(a.ausgabe + ".mpd", "w").write("\n".join(out) + "\n")
    rows = ["LDraw Part,BrickLink ID,Farbe,Menge"]; xml = ["<INVENTORY>"]
    for (nm, c), qn in sorted(bom.items()):
        bl = BL_ID.get(nm, nm)
        rows.append(f"{nm}.dat,{bl},{PALETTE[c][0]},{qn}")
        xml.append(f"<ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID><COLOR>{PALETTE[c][1]}</COLOR><MINQTY>{qn}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    open(a.ausgabe + "_bom.csv", "w").write("\n".join(rows) + "\n")
    open(a.ausgabe + "_bricklink.xml", "w").write("\n".join(xml) + "\n")
    prev = Image.new("RGB", (W, H))
    for q, c in col.items(): prev.putpixel(q, PALETTE[c][2])
    prev.resize((W * 10, H * 10), Image.NEAREST).save(a.ausgabe + "_vorschau.png")
    print(f"{W}x{H} Noppen | Teile {sum(bom.values())} | Positionen {len(bom)} | Farben {len({c for _, c in bom})}")


if __name__ == "__main__":
    main()
