"""
Mosaik-Generator fuer 1x1-Fliesen (Graustufen-Vorlagen)
======================================================
Erzeugt aus einem Bild ein N x N Raster aus LEGO-Farben und bewertet jede Variante gegen die Vorlage:
  - "fern":   Abweichung in L* nach leichter Unschaerfe (so wirkt ein Mosaik aus Betrachtungsabstand)
  - "detail": strukturelle Aehnlichkeit (SSIM) im Raster selbst
Aufruf:
  python3 make_mosaic.py <bild> <ausgabe.txt> [--size 60] [--variant NAME] [--compare vorschau_dir]
Die Ausgabe ist eine Textdatei mit N Zeilen zu N Zeichen (Farbkuerzel siehe PALETTES).
"""
import argparse, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# echte LEGO-Farben (sRGB, Rebrickable/BrickLink); Kuerzel -> (LDraw-Code, Name, Hex)
COLORS = {
    "K": (0, "Black", "05131D"),
    "P": (148, "Pearl Dark Gray", "575857"),
    "D": (72, "Dark Bluish Gray", "6C6E68"),
    "S": (179, "Flat Silver", "898788"),
    "L": (71, "Light Bluish Gray", "A0A5A9"),
    "W": (15, "White", "FFFFFF"),
}
PALETTES = {"4": "KDLW", "5s": "KDSLW", "5p": "KPDLW", "6": "KPDSLW"}


def srgb_to_lin(c):
    c = np.asarray(c, dtype=float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_lstar(y):
    y = np.clip(y, 0, 1)
    f = np.where(y > (6 / 29) ** 3, np.cbrt(y), y / (3 * (6 / 29) ** 2) + 4 / 29)
    return 116 * f - 16


def hex_lin(h):
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    lin = srgb_to_lin(rgb)
    return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])


def gauss(a, sigma):
    if sigma <= 0: return a
    r = int(math.ceil(3 * sigma)); x = np.arange(-r, r + 1)
    k = np.exp(-x ** 2 / (2 * sigma ** 2)); k /= k.sum()
    p = np.pad(a, r, mode="reflect")
    p = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 0, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 1, p)


def ssim(a, b, sigma=1.5, L=100.0):
    c1, c2 = (0.01 * L) ** 2, (0.03 * L) ** 2
    ma, mb = gauss(a, sigma), gauss(b, sigma)
    va = gauss(a * a, sigma) - ma ** 2; vb = gauss(b * b, sigma) - mb ** 2; cov = gauss(a * b, sigma) - ma * mb
    s = ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))
    return float(s.mean())


def target(img_path, size, levels=(0, 100), gamma=1.0, sharpen=0.0, hl=(1.0, 0.6), lc=0.0):
    """Vorlage -> Raster (lineares Licht).
    sharpen: Unscharf-Maskierung (fein), lc: Lokalkontrast (grob, ~2 Zellen),
    hl=(gain, schwelle): Lichter oberhalb der Schwelle werden gestreckt (Metall-Glanz)"""
    im = Image.open(img_path).convert("L")
    if sharpen > 0:
        im = im.filter(ImageFilter.UnsharpMask(radius=6, percent=int(sharpen * 100), threshold=0))
    if lc > 0:
        im = im.filter(ImageFilter.UnsharpMask(radius=18, percent=int(lc * 100), threshold=0))
    a = np.asarray(im, dtype=float)
    lo, hi = np.percentile(a, levels[0]), np.percentile(a, levels[1])
    a = np.clip((a - lo) / max(1e-6, hi - lo), 0, 1) ** gamma
    g, t = hl
    a = np.clip(np.where(a > t, t + (a - t) * g, a), 0, 1) * 255
    lin = srgb_to_lin(a)
    # Flaechenmittel in linearem Licht (optische Mischung)
    small = np.asarray(Image.fromarray(lin.astype(np.float32), mode="F").resize((size, size), Image.BOX))
    return small


def reference(img_path, size):
    """unveraenderte Vorlage im Raster (lineares Licht) - Massstab fuer den Vergleich"""
    return target(img_path, size)


def quantize(lin, pal, dither=0.0, serpentine=True):
    pl = np.array([hex_lin(COLORS[c][2]) for c in pal])
    pL = lin_to_lstar(pl)
    work = lin_to_lstar(lin).copy()
    n = work.shape[0]
    out = np.empty(work.shape, dtype="<U1")
    for y in range(n):
        xs = range(n) if (not serpentine or y % 2 == 0) else range(n - 1, -1, -1)
        d = 1 if (not serpentine or y % 2 == 0) else -1
        for x in xs:
            v = work[y, x]
            i = int(np.argmin(np.abs(pL - v)))
            out[y, x] = pal[i]
            e = (v - pL[i]) * dither
            if e == 0: continue
            for dx, dy, w in ((d, 0, 7), (-d, 1, 3), (0, 1, 5), (d, 1, 1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < n and yy < n: work[yy, xx] += e * w / 16
    return out


def cleanup(grid, pal, passes=1):
    """entfernt isolierte Einzelfliesen: Zelle, deren 4 Nachbarn alle eine andere, gemeinsame
    Mehrheitsfarbe haben (mind. 3 von 4), bekommt diese Farbe"""
    g = grid.copy(); n = g.shape[0]
    for _ in range(passes):
        h = g.copy()
        for y in range(n):
            for x in range(n):
                nb = [g[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < n and 0 <= xx < n]
                if g[y, x] in nb: continue
                best = max(set(nb), key=nb.count)
                if nb.count(best) >= 3: h[y, x] = best
        g = h
    return g


def grid_lin(grid):
    return np.vectorize(lambda c: hex_lin(COLORS[c][2]))(grid)


def score(grid, ref_lin):
    g = grid_lin(grid)
    far = float(np.sqrt(np.mean((lin_to_lstar(gauss(g, 1.2)) - lin_to_lstar(gauss(ref_lin, 1.2))) ** 2)))
    det = ssim(lin_to_lstar(g), lin_to_lstar(ref_lin))
    return far, det


def preview(grid, path, cell=8, ref=None):
    n = grid.shape[0]
    im = Image.new("RGB", (n * cell + (n * cell + 20 if ref else 0), n * cell), (40, 40, 40))
    d = ImageDraw.Draw(im)
    for y in range(n):
        for x in range(n):
            h = COLORS[grid[y, x]][2]
            d.rectangle([x * cell, y * cell, x * cell + cell - 2, y * cell + cell - 2],
                        fill=tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    if ref:
        r = Image.open(ref).convert("RGB").resize((n * cell, n * cell), Image.LANCZOS)
        im.paste(r, (n * cell + 20, 0))
    im.save(path)


VARIANTS = {
    # name: (palette, levels, gamma, sharpen, dither[, hl, lc])
    "nearest4":        ("4", (0, 100), 1.0, 0.0, 0.0),
    "fs4":             ("4", (0, 100), 1.0, 0.0, 1.0),
    "fs4_soft":        ("4", (0, 100), 1.0, 0.0, 0.6),
    "fs4_levels":      ("4", (0.5, 99.5), 1.0, 0.0, 0.6),
    "fs4_levels_g":    ("4", (0.5, 99.5), 0.85, 0.0, 0.6),
    "fs4_sharp":       ("4", (0.5, 99.5), 0.85, 0.6, 0.6),
    "fs5p_soft":       ("5p", (0, 100), 1.0, 0.0, 0.6),
    "fs5s_soft":       ("5s", (0, 100), 1.0, 0.0, 0.6),
    "fs5p_sharp":      ("5p", (0.5, 99.5), 0.9, 0.6, 0.6),
    "fs6_soft":        ("6", (0, 100), 1.0, 0.0, 0.6),
    # Runde 2: Lichter anheben (Grill), Lokalkontrast
    "fs4_hl":          ("4", (0, 100), 1.0, 0.0, 0.6, (1.5, 0.55), 0.0),
    "fs4_hl_lc":       ("4", (0, 100), 1.0, 0.0, 0.6, (1.5, 0.55), 0.5),
    "near4_hl_lc":     ("4", (0, 100), 1.0, 0.0, 0.0, (1.5, 0.55), 0.5),
    "fs5p_hl":         ("5p", (0, 100), 1.0, 0.0, 0.6, (1.5, 0.55), 0.0),
    "fs5p_hl_lc":      ("5p", (0, 100), 1.0, 0.0, 0.6, (1.5, 0.55), 0.5),
    "fs5p_hl_lc_s":    ("5p", (0, 100), 1.0, 0.4, 0.5, (1.6, 0.5), 0.5),
    "near5p_hl_lc":    ("5p", (0, 100), 1.0, 0.0, 0.0, (1.5, 0.55), 0.5),
    # Runde 3: nur Standardfarben, Tonwerte feiner abgestimmt, Einzelfliesen bereinigt ("_c")
    "n4_a":            ("4", (0, 100), 0.90, 0.0, 0.0, (1.5, 0.55), 0.5),
    "n4_a_c":          ("4", (0, 100), 0.90, 0.0, 0.0, (1.5, 0.55), 0.5),
    "n4_b_c":          ("4", (0, 100), 0.90, 0.0, 0.3, (1.5, 0.55), 0.3),
    "n4_c_c":          ("4", (0, 100), 1.00, 0.0, 0.3, (1.6, 0.50), 0.5),
    "n4_d_c":          ("4", (0, 100), 0.85, 0.0, 0.0, (1.4, 0.60), 0.6),
    "n5p_c":           ("5p", (0, 100), 1.0, 0.0, 0.0, (1.5, 0.55), 0.5),
}


def run(img, size, name):
    v = VARIANTS[name]
    pal, lev, gam, shp, dit = v[:5]
    hl, lc = (v[5], v[6]) if len(v) > 5 else ((1.0, 0.6), 0.0)
    grid = quantize(target(img, size, lev, gam, shp, hl, lc), PALETTES[pal], dit)
    if name.endswith("_c"): grid = cleanup(grid, PALETTES[pal])
    return grid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("out")
    ap.add_argument("--size", type=int, default=60)
    ap.add_argument("--variant", default=None)
    ap.add_argument("--compare", default=None, help="Ordner fuer Vorschaubilder aller Varianten")
    a = ap.parse_args()
    ref = reference(a.image, a.size)
    names = [a.variant] if a.variant else list(VARIANTS)
    results = {}
    for nm in names:
        g = run(a.image, a.size, nm)
        far, det = score(g, ref)
        cnt = {c: int((g == c).sum()) for c in sorted(set(g.flatten()))}
        results[nm] = (far, det, cnt, g)
        print(f"{nm:14s} fern(dL*)={far:5.2f}  detail(SSIM)={det:.3f}  {cnt}")
        if a.compare:
            os.makedirs(a.compare, exist_ok=True)
            preview(g, os.path.join(a.compare, f"{nm}.png"), ref=a.image)
    best = min(results, key=lambda k: results[k][0] - 20 * results[k][1])
    print("beste Variante:", best)
    g = results[a.variant or best][3]
    with open(a.out, "w") as f:
        f.write("\n".join("".join(r) for r in g) + "\n")
