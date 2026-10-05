"""
Blueprint und Ansichten aus layout.json (vom Generator geschrieben):
  blueprint_topdown.png  – Draufsicht 128 x 64 Noppen mit Raster, Zonen, Koepfen, Lift, Pyro, LED, Tuermen
  elevation_front.png    – Frontansicht (Blick von Y = 63 nach hinten), Hoehen in Steinen
  elevation_side.png     – Seitenansicht (Blick von X = 127 nach links)
  elevation_rear.png     – Rueckansicht (Blick von Y = 0 nach vorne)
Jede Ansicht: Noppen-Raster, Hoehenlinien je Stein, farbig nach Modul.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, "layout.json")))
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    FONTB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    FONTS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except OSError:
    FONT = FONTB = FONTS = ImageFont.load_default()

MODCOL = {"00_BASE": (40, 40, 44), "01_MAIN_STAGE": (120, 128, 140), "02_FISSURE": (70, 74, 82),
          "03_ROCK_LEFT": (95, 90, 84), "04_ROCK_RIGHT": (95, 90, 84), "05_MAIN_ROCK": (110, 104, 96),
          "06_HEAD_A": (190, 170, 120), "07_HEAD_B": (175, 155, 110), "08_HEAD_C": (160, 140, 100),
          "09_LED_SYSTEM": (40, 90, 170), "10_LIGHTING": (240, 230, 120), "11_SPEAKERS": (150, 60, 160),
          "12_PYRO": (240, 120, 30), "13_LIFT": (60, 170, 160), "14_TECHNICAL_RIG": (90, 150, 220),
          "15_FINAL_DETAILS": (220, 70, 70)}
S = 10                                     # Pixel je Noppe
M = 60                                     # Rand


def grid(d, w, h, x0, y0, step_x=8, step_y=8, labels=True):
    for X in range(0, w + 1):
        c = (200, 200, 205) if X % step_x else (150, 150, 160)
        d.line([(x0 + X * S, y0), (x0 + X * S, y0 + h * S)], fill=c, width=1)
        if labels and X % step_x == 0 and X < w: d.text((x0 + X * S + 2, y0 - 16), str(X), fill=(60, 60, 70), font=FONTS)
    for Y in range(0, h + 1):
        c = (200, 200, 205) if Y % step_y else (150, 150, 160)
        d.line([(x0, y0 + Y * S), (x0 + w * S, y0 + Y * S)], fill=c, width=1)
        if labels and Y % step_y == 0 and Y < h: d.text((x0 - 26, y0 + Y * S + 1), str(Y), fill=(60, 60, 70), font=FONTS)


def topdown():
    W, H = 128, 64
    im = Image.new("RGB", (W * S + 2 * M + 300, H * S + 2 * M + 40), (250, 250, 252))
    d = ImageDraw.Draw(im)
    x0, y0 = M, M
    kindcol = {"weg": (80, 84, 92), "lift": (60, 170, 160), "plateau": (150, 158, 170), "bstage": (150, 158, 170),
               "rear": (90, 150, 220), "kopfsockel": (130, 122, 110), "fels": None}
    hmax = max(c[2] for c in L["cells"])
    for X, Y, h, kind, mod in L["cells"]:
        col = kindcol.get(kind)
        if col is None:
            t = h / hmax; col = (int(70 + 90 * t), int(66 + 84 * t), int(60 + 76 * t))
        d.rectangle([x0 + X * S, y0 + Y * S, x0 + X * S + S - 1, y0 + Y * S + S - 1], fill=col)
    grid(d, W, H, x0, y0)
    d.rectangle([x0, y0, x0 + W * S, y0 + H * S], outline=(0, 0, 0), width=2)

    def box(X, Y, w, h, col, text=None, fill=None, width=3):
        d.rectangle([x0 + X * S, y0 + Y * S, x0 + (X + w) * S, y0 + (Y + h) * S], outline=col, width=width, fill=fill)
        if text: d.text((x0 + X * S + 3, y0 + Y * S + 2), text, fill=col if not fill else (255, 255, 255), font=FONT)

    def dot(X, Y, col, r=4):
        cx, cy = x0 + (X + 0.5) * S, y0 + (Y + 0.5) * S
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(0, 0, 0))
    for m, X0, Y0, w, dp, rot, ph in L["heads"]:
        box(X0, Y0, w, dp, (150, 90, 0), m.split("_")[0] + " " + m.split("_")[-1])
        fx = X0 + w / 2; fy = Y0 + dp + 1.2 if rot == 180 else Y0 - 1.2
        d.text((x0 + fx * S - 18, y0 + fy * S - 7), "Blick", fill=(150, 90, 0), font=FONTS)
    lx = [c[0] for c in L["lift"]]; ly = [c[1] for c in L["lift"]]
    box(min(lx), min(ly), max(lx) - min(lx) + 1, max(ly) - min(ly) + 1, (0, 130, 120), "13 LIFT")
    for c in L["pyro_a"] + L["pyro_ridge"] + L["pyro_fiss"]: dot(c[0], c[1], (240, 120, 30))
    for c in L["lasers"]: dot(c[0], c[1], (40, 200, 60))
    for X, Y in L["racks"]: box(X, Y, 2, 4, (240, 120, 30), "P4")
    for X0, Y0, rot in L["leds"]: box(X0, Y0, 2, L["led_w"], (40, 90, 170), None, fill=(40, 90, 170))
    for X, Y in L["light_towers"]: box(X - 2, Y, 6, 2, (180, 160, 0), "L")
    for X, Y, f in L["speakers"]: box(X, Y, 2, 2, (150, 60, 160), "S", fill=(150, 60, 160))
    fx = [c[0] for c in L["foh"]]; fy = [c[1] for c in L["foh"]]
    box(min(fx), min(fy), max(fx) - min(fx) + 1, max(fy) - min(fy) + 1, (90, 150, 220), "FOH")
    box(L["drop_tower"][0], L["drop_tower"][1], 4, 4, (220, 70, 70), "DROP", fill=(220, 70, 70))
    # Zonenbeschriftung
    for X, Y, t in ((24, 31, "FISSURE / Laufweg (Deck 3 Steine)"), (5, 41, "PLAZA A"), (108, 41, "B-STAGE"),
                    (119, 26, "REAR"), (2, 21, "03 ROCK LEFT"), (52, 7, "05 MAIN ROCK"), (95, 8, "04 ROCK RIGHT")):
        d.text((x0 + X * S, y0 + Y * S), t, fill=(0, 0, 0), font=FONTB)
    d.text((x0, 12), "TOP-DOWN BLUEPRINT – Travis Scott UTOPIA Circus Maximus – MetLife Stadium 09.10.2024 – 128 x 64 Noppen"
           "  (X nach rechts, Y nach unten = vorne)", fill=(0, 0, 0), font=FONTB)
    lg = [((80, 84, 92), "Laufweg / Fissure (Deck 9 P)"), ((150, 158, 170), "Plateau / B-Stage (12 P)"),
          ((140, 130, 115), "Fels (heller = hoeher)"), ((150, 90, 0), "Kopf-Fussabdruck"), ((0, 130, 120), "Lift"),
          ((240, 120, 30), "Pyro (P1 Kopf A, P2 Grat, P3 Fissure, P4 Racks)"), ((40, 200, 60), "Laser"),
          ((40, 90, 170), "LED-Panel (Stirnseiten)"), ((180, 160, 0), "Lichtturm"), ((150, 60, 160), "Lautsprecherturm"),
          ((90, 150, 220), "Technik / FOH / Rear"), ((220, 70, 70), "Freifallturm (MetLife)")]
    lx0 = x0 + W * S + 20
    for n, (c, t) in enumerate(lg):
        d.rectangle([lx0, y0 + n * 24, lx0 + 16, y0 + n * 24 + 16], fill=c, outline=(0, 0, 0))
        d.text((lx0 + 22, y0 + n * 24 + 1), t, fill=(0, 0, 0), font=FONTS)
    im.save(os.path.join(HERE, "blueprint_topdown.png"))


def elevation(view):
    """view: front (von Y=63), rear (von Y=0), side (von X=127)"""
    near = {}
    for sub, cells, ytop, ybot in L["occ"]:
        for X, Y in cells:
            for lv in range(int(-ybot) // 8, int(-ytop) // 8 + (1 if (-ytop) % 8 else 0)):
                if lv < 0: continue
                if view == "front": u, depth = X, Y
                elif view == "rear": u, depth = 127 - X, -Y
                else: u, depth = Y, X
                key = (u, lv)
                if key not in near or depth > near[key][0]: near[key] = (depth, sub)
    W = 128 if view != "side" else 64
    HL = max(k[1] for k in near) + 4
    sx, sy = S, S * 8 // 20 * 1          # 1 Platte = 8 LDU, 1 Noppe = 20 LDU -> massstaeblich
    sy = 4
    im = Image.new("RGB", (W * sx + 2 * M + 80, HL * sy + 2 * M + 30), (250, 250, 252))
    d = ImageDraw.Draw(im)
    x0, yb = M + 30, M + HL * sy
    dmin = min(v[0] for v in near.values()); dmax = max(v[0] for v in near.values())
    for (u, lv), (depth, sub) in near.items():
        c = MODCOL.get(sub, (120, 120, 120))
        f = 0.55 + 0.45 * (depth - dmin) / max(1, dmax - dmin)
        c = tuple(int(v * f) for v in c)
        d.rectangle([x0 + u * sx, yb - (lv + 1) * sy, x0 + u * sx + sx - 1, yb - lv * sy - 1], fill=c)
    for X in range(0, W + 1, 8):
        d.line([(x0 + X * sx, yb), (x0 + X * sx, yb + 6)], fill=(0, 0, 0))
        d.text((x0 + X * sx - 6, yb + 8), str(X), fill=(0, 0, 0), font=FONTS)
    for g in range(0, HL // 3 + 1):
        y = yb - g * 3 * sy
        d.line([(x0 - 6, y), (x0 + W * sx, y)], fill=(215, 215, 220) if g % 5 else (170, 170, 180))
        if g % 5 == 0: d.text((x0 - 34, y - 6), f"{g} St", fill=(0, 0, 0), font=FONTS)
    title = {"front": "FRONT ELEVATION (Blick von vorne, Y = 63)", "rear": "REAR ELEVATION (Blick von hinten, Y = 0; X gespiegelt)",
             "side": "SIDE ELEVATION (Blick vom rechten Ende, X = 127; horizontal = Y)"}[view]
    d.text((x0, 14), title + " – Hoehen in Steinen (St), Raster in Noppen", fill=(0, 0, 0), font=FONTB)
    used = sorted(set(v[1] for v in near.values()))
    for n, sub in enumerate(used):
        xx = x0 + (n % 6) * 170; yy = 34 + (n // 6) * 16
        d.rectangle([xx, yy, xx + 12, yy + 12], fill=MODCOL.get(sub, (120, 120, 120)))
        d.text((xx + 16, yy - 1), sub, fill=(0, 0, 0), font=FONTS)
    im.save(os.path.join(HERE, f"elevation_{view}.png"))


topdown()
for v in ("front", "side", "rear"): elevation(v)
print("Blueprint und Ansichten geschrieben")
