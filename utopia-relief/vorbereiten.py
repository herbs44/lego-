# UTOPIA-Cover vorbereiten: Low-Key-Foto aufhellen, Muskeln betonen, Haut warm, Hose silbern
# Aufruf: python3 vorbereiten.py cover.png hell.png   (Koordinaten fuer ein 300-px-Cover, skaliert automatisch)
import sys; from PIL import Image, ImageFilter, ImageDraw; import numpy as np
im = Image.open(sys.argv[1]).convert("RGB")
a = np.asarray(im).astype(float); l = a.mean(2)
bl = np.asarray(Image.fromarray(l.astype("uint8")).filter(ImageFilter.GaussianBlur(2.5))).astype(float)
b4 = np.asarray(Image.fromarray(l.astype("uint8")).filter(ImageFilter.GaussianBlur(4))).astype(float)
maske = (l > 12) | ((l > 8.3) & (b4 > 9.3))                      # dunkler Unterarm haengt am Rest
arm = Image.new("L", im.size); ImageDraw.Draw(arm).polygon([(x * im.size[0] / 300, y * im.size[1] / 300) for x, y in [(80, 97), (95, 94), (110, 136), (99, 138)]], fill=1)
arm = np.asarray(arm) > 0   # Unterarm im Schatten (nur Streiflicht im Foto)
maske = maske | arm
l = np.where(arm, np.maximum(l, 16), l)
ld = np.where(maske, l + 0.8 * (l - bl), 0)                     # lokaler Kontrast (Bauchmuskeln, Rippen)
t = np.where(maske, np.clip((np.maximum(ld, 13) - 9) / (150 - 9), 0, 1) ** 0.45, 0)
H, W = l.shape; yy, xx = np.mgrid[0:H, 0:W] / H
hose = (yy > 0.835) & (xx < 0.75)                                 # Hose unten Mitte
haut = ([0, .09, .22, .40, .60, .84, 1.02],
        [(0,0,0), (53,33,0), (88,42,18), (170,125,85), (208,145,104), (246,215,179), (244,244,244)])
grau = ([0, .38, .55, .72, .92], [(0,0,0), (84,89,92), (137,135,136), (160,165,169), (244,244,244)])
def ramp(st, cols): c = np.array(cols, float); return np.stack([np.interp(t, st, c[:, k]) for k in range(3)], 2)
boden = (xx > 0.70) & (yy > 0.70) & (xx - 0.70 > (yy - 0.70) * 0.2)   # heller Boden rechts unten -> schwarz
t = np.where(boden, 0, t)
out = np.where(hose[..., None], ramp(*grau), ramp(*haut))
Image.fromarray(out.astype("uint8")).save(sys.argv[2])
