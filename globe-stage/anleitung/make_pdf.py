"""
Bauanleitung als PDF (A4 quer) aus den geplanten und gerenderten Schritten
=========================================================================
Aufruf: python3 make_pdf.py <build-ordner> <ausgabe.pdf>
Erwartet im build-ordner: steps.json, shots/*.png (Schritte + cover/sec_*), thumbs/*.png
"""
import csv, io, json, math, os, runpy, sys, contextlib, datetime
from collections import Counter, defaultdict
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white, black

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "build")
OUTPDF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "Bauanleitung_Globe_Stage.pdf")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DV", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DVB", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))

# ---------------- Daten ----------------
D = json.load(open(os.path.join(BUILD, "steps.json")))
STEPS = D["steps"]
_argv = sys.argv; sys.argv = ["gen", os.path.join(BUILD, "_gen")]
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(HERE, "..", "generate_globe_stage.py"))
sys.argv = _argv
parts = G["parts"]; COLORS = G["COLORS"]
assert len(parts) == sum(len(s["ids"]) for s in STEPS), "Teileliste passt nicht zu steps.json"
NAMES = {}
for r in csv.DictReader(open(os.path.join(HERE, "..", "globe_stage_bom.csv"))):
    NAMES[r["LDraw Part"].replace(".dat", "")] = (r["Name"], r["BrickLink ID"])
MOSAIC = [l.strip() for l in open(os.path.join(HERE, "..", "bully_mosaik_60x60.txt")) if l.strip()]
MCOL = {"K": ("Black", "#1B2A34", "#FFFFFF"), "D": ("Dark Bluish Gray", "#6C6E68", "#FFFFFF"),
        "L": ("Light Bluish Gray", "#A0A5A9", "#1B2A34"), "W": ("White", "#FFFFFF", "#1B2A34")}

W, H = landscape(A4)
M = 28
INK = HexColor("#1B2A34"); MUTED = HexColor("#5A6670"); LINE = HexColor("#D5DBE0")
PANEL = HexColor("#F1F3F5"); ACCENT = HexColor("#F2B700"); NOTE = HexColor("#FFF6D6"); OKG = HexColor("#2E8540")
SEC_INFO = {
    "A": ("Basis und Kuppel", "Grundplatten, Basis, Laufsteg, LED-Ring mit Kanal für den LED-Streifen und die "
          "Erdkugel-Kuppel mit Innenstützen, Rundung aus 1×1-Teilen und Nebel. Gebaut wird Lage für Lage von unten."),
    "B": ("Ecktürme", "Vier Türme aus Gitterträgern an den Ecken der Grundplatten. Bis das Dach aufliegt, stehen sie "
          "frei – vorsichtig behandeln."),
    "C": ("Truss-Ring (Baugruppe)", "Der Lichtring wird separat auf dem Tisch gebaut: Bodenplatten, Wände, 24 Scheinwerfer "
          "mit LEDs und Obergurt. Er wird erst in der Endmontage eingesetzt."),
    "D": ("Dach mit Mosaik (Baugruppe)", "Das Dach wird separat gebaut: Decke, versetzte Dachplatten, Attika und das "
          "Album-Cover als Mosaik aus 3.600 Fliesen 1×1."),
    "E": ("Endmontage", "Truss-Ring auf Hilfsstützen einsetzen, Dach aufsetzen, Ring an die Seile hängen, Kabel anschließen."),
}

_img_cache = {}
def img(path, quality=66, trim=False, bgfill=None, maxw=950):
    key = (path, trim, bgfill, maxw)
    if key in _img_cache: return _img_cache[key]
    im = Image.open(path).convert("RGB")
    if trim:
        bg = Image.new("RGB", im.size, (255, 255, 255))
        from PIL import ImageChops
        bb = ImageChops.difference(im, bg).getbbox()
        if bb:
            pad = 6; bb = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))
            im = im.crop(bb)
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    if bgfill:
        from PIL import ImageDraw
        for pt in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
            if im.getpixel(pt) == (255, 255, 255): ImageDraw.floodfill(im, pt, bgfill, thresh=10)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=quality, optimize=True); buf.seek(0)
    r = (ImageReader(buf), im.size)
    _img_cache[key] = r
    return r


def draw_img(c, path, x, y, w, h, trim=False, align="center", bgfill=None, maxw=950):
    """Bild in Rahmen (x,y unten links, w,h) einpassen"""
    if not os.path.exists(path):
        c.setStrokeColor(LINE); c.rect(x, y, w, h, stroke=1, fill=0); return w, h
    ir, (iw, ih) = img(path, trim=trim, bgfill=bgfill, maxw=maxw)
    s = min(w / iw, h / ih); dw, dh = iw * s, ih * s
    dx = x + (w - dw) / 2 if align == "center" else x
    c.drawImage(ir, dx, y + (h - dh) / 2, dw, dh)
    return dw, dh


def wrap(text, font, size, width):
    words = text.split(); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if pdfmetrics.stringWidth(t, font, size) <= width: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines


def para(c, text, x, y, width, font="DV", size=10, leading=None, color=INK):
    leading = leading or size * 1.35
    c.setFont(font, size); c.setFillColor(color)
    for ln in wrap(text, font, size, width):
        c.drawString(x, y, ln); y -= leading
    return y


def footer(c, page, sec=None):
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(M, 22, W - M, 22)
    c.setFont("DV", 7.5); c.setFillColor(MUTED)
    c.drawString(M, 11, "Globe Stage – Bauanleitung")
    if sec: c.drawCentredString(W / 2, 11, f"Abschnitt {sec}: {SEC_INFO[sec][0]}")
    c.drawRightString(W - M, 11, f"Seite {page}")


def thumb_path(nm, col): return os.path.join(BUILD, "thumbs", f"t_{nm}_{col}.png")
def shot(name): return os.path.join(BUILD, "shots", f"{name}.png")


def callout_items(ids):
    cnt = Counter((parts[i].name, parts[i].color) for i in ids)
    return sorted(cnt.items(), key=lambda kv: (kv[0][0], kv[0][1]))


def draw_callout(c, items, x, y_top, width, max_h):
    """Teile-Kasten: Bild + Anzahl, fliessend. Liefert benutzte Hoehe."""
    n = len(items)
    if n == 0: return 0
    for ts in (46, 40, 34, 29, 25):
        cw = ts + 8; cols = max(1, int((width - 12) // cw)); rows = math.ceil(n / cols)
        hgt = rows * (ts + 14) + 10
        if hgt <= max_h: break
    c.setFillColor(PANEL); c.setStrokeColor(LINE); c.roundRect(x, y_top - hgt, width, hgt, 6, stroke=1, fill=1)
    for k, ((nm, col), q) in enumerate(items):
        r, cc = divmod(k, cols)
        tx = x + 8 + cc * cw; ty = y_top - 6 - (r + 1) * (ts + 14) + 14
        p = thumb_path(nm, col)
        if os.path.exists(p): draw_img(c, p, tx, ty, ts, ts, trim=True, bgfill=(241, 243, 245))
        c.setFont("DVB", 7.5 if ts > 30 else 6.5); c.setFillColor(INK)
        c.drawCentredString(tx + ts / 2, ty - 9, f"{q}×")
    return hgt


def draw_step(c, n, st, x, y_top, width, height):
    """ein Schritt in einer Spalte"""
    y = y_top
    c.setFillColor(INK); c.setFont("DVB", 26); c.drawString(x, y - 24, str(n + 1))
    nw = pdfmetrics.stringWidth(str(n + 1), "DVB", 26)
    c.setFont("DV", 9.5); c.setFillColor(MUTED)
    tl = wrap(st["title"], "DV", 9.5, width - nw - 12)
    for k, ln in enumerate(tl[:2]): c.drawString(x + nw + 10, y - 13 - k * 11, ln)
    y -= 34
    items = callout_items(st["ids"])
    if items:
        y -= draw_callout(c, items, x, y, width, 150) + 6
    note_h = 0
    if st.get("action"):
        lines = wrap(st["action"], "DV", 8.5, width - 30)
        note_h = len(lines) * 11 + 14
    img_h = y - (y_top - height) - note_h - (6 if note_h else 0)
    if os.path.exists(shot(f"s{n + 1:03d}")):
        draw_img(c, shot(f"s{n + 1:03d}"), x, y - img_h, width, img_h, trim=True, maxw=860)
    y -= img_h + 6
    if note_h:
        c.setFillColor(NOTE); c.setStrokeColor(ACCENT); c.setLineWidth(0.8)
        c.roundRect(x, y - note_h, width, note_h, 5, stroke=1, fill=1)
        c.setFillColor(ACCENT); c.setFont("DVB", 11); c.drawString(x + 8, y - 15, "!")
        para(c, st["action"], x + 22, y - 13, width - 30, size=8.5, leading=11)


def mosaic_chart(c, r0, r1, x, y_top, width, show_all_faded=False):
    """Plan fuer Reihen r0..r1-1 (60 Spalten), Buchstaben in den Feldern"""
    ncol = 60; lab = 18
    cs = (width - lab) / ncol
    rows = range(r0, r1)
    c.setFont("DV", 6)
    for q in range(ncol):
        if q % 5 == 4 or q == 0:
            c.setFillColor(MUTED); c.drawCentredString(x + lab + (q + 0.5) * cs, y_top - 7, str(q + 1))
    y0 = y_top - 11
    for k, r in enumerate(rows):
        yy = y0 - (k + 1) * cs
        c.setFillColor(MUTED); c.setFont("DV", 6.5); c.drawRightString(x + lab - 3, yy + cs * 0.3, str(r + 1))
        for q in range(ncol):
            ch = MOSAIC[r][q]; _, fill, txt = MCOL[ch]
            c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor("#9AA3AA")); c.setLineWidth(0.25)
            c.rect(x + lab + q * cs, yy, cs, cs, stroke=1, fill=1)
            if cs >= 9:
                c.setFillColor(HexColor(txt)); c.setFont("DV", min(7, cs * 0.55))
                c.drawCentredString(x + lab + (q + 0.5) * cs, yy + cs * 0.3, ch)
        if (r + 1) % 5 == 0:
            c.setStrokeColor(INK); c.setLineWidth(0.8); c.line(x + lab, yy, x + lab + ncol * cs, yy)
    for q in range(0, ncol + 1, 5):
        c.setStrokeColor(INK); c.setLineWidth(0.8 if q % 10 == 0 else 0.4)
        c.line(x + lab + q * cs, y0, x + lab + q * cs, y0 - len(rows) * cs)
    return 11 + len(rows) * cs


# ---------------- Seitenplan ----------------
pages = []   # (typ, daten)
pages.append(("cover", None)); pages.append(("inhalt", None)); pages.append(("pruefung", None))
sec_first_page = {}
by_sec = defaultdict(list)
for n, st in enumerate(STEPS): by_sec[st["sec"]].append(n)
for sec in "ABCDE":
    sec_first_page[sec] = len(pages) + 1
    pages.append(("abschnitt", sec))
    ns = by_sec[sec]; k = 0
    while k < len(ns):
        st = STEPS[ns[k]]
        if st["kind"] == "mosaik":
            if st["chart"][0] == 0: pages.append(("mosaik_gesamt", None))
            pages.append(("mosaik", ns[k])); k += 1
        elif k + 1 < len(ns) and STEPS[ns[k + 1]]["kind"] != "mosaik":
            pages.append(("zwei", (ns[k], ns[k + 1]))); k += 2
        else:
            pages.append(("eins", ns[k])); k += 1
pages.append(("fertig", None))
bom_first = len(pages) + 1
BOM = sorted(Counter((p.name, p.color) for p in parts).items(), key=lambda kv: (kv[0][0], kv[0][1]))
PER = 40
for k in range(0, len(BOM), PER): pages.append(("stueckliste", k))
TOTAL = len(pages)
step_page = {}
for pno, (t, d) in enumerate(pages, 1):
    if t == "zwei": step_page[d[0]] = step_page[d[1]] = pno
    elif t in ("eins", "mosaik"): step_page[d] = pno

# ---------------- Zeichnen ----------------
c = canvas.Canvas(OUTPDF, pagesize=(W, H))
c.setTitle("Globe Stage – Bauanleitung"); c.setAuthor("Claude Code (generiert)")
c.setSubject("LEGO-MOC Bauanleitung mit geprüften Bauschritten")
n_parts = len(parts); n_steps = len(STEPS)

for pno, (typ, dat) in enumerate(pages, 1):
    if typ == "cover":
        c.setFillColor(INK); c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFillColor(white); c.rect(0, 0, W * 0.62, H, stroke=0, fill=1)
        draw_img(c, shot("cover"), 10, 30, W * 0.62 - 20, H - 60, trim=True, maxw=1400)
        x = W * 0.62 + 30; wtxt = W - x - 30
        c.setFillColor(ACCENT); c.rect(x, H - 118, 44, 5, stroke=0, fill=1)
        c.setFillColor(white); c.setFont("DVB", 34); c.drawString(x, H - 160, "GLOBE")
        c.drawString(x, H - 198, "STAGE")
        c.setFont("DV", 13); c.drawString(x, H - 226, "Bauanleitung · LEGO-MOC")
        facts = [(f"{n_parts:,}".replace(",", "."), "Teile"), (str(n_steps), "Schritte"),
                 ("51 × 51 × 41 cm", "Grundfläche × Höhe"), ("5", "Bauabschnitte")]
        yy = H - 290
        for v, t in facts:
            c.setFont("DVB", 16); c.setFillColor(white); c.drawString(x, yy, v)
            c.setFont("DV", 9); c.setFillColor(HexColor("#AEB8C0")); c.drawString(x, yy - 13, t); yy -= 44
        c.setFont("DV", 8.5); c.setFillColor(HexColor("#AEB8C0"))
        para(c, "Alle Bauschritte wurden automatisch auf Verbindung, Einsetzbarkeit und Endmontage geprüft.",
             x, 80, wtxt, size=8.5, color=HexColor("#AEB8C0"))
        c.drawString(x, 40, f"Stand {datetime.date.today().strftime('%d.%m.%Y')} · generiert aus globe_stage.mpd")
    elif typ == "inhalt":
        c.setFillColor(INK); c.setFont("DVB", 20); c.drawString(M, H - M - 20, "Übersicht und Vorbereitung")
        colw = (W - 2 * M - 30) / 2
        y = H - M - 56
        c.setFont("DVB", 12); c.drawString(M, y, "Bauabschnitte"); y -= 20
        for sec in "ABCDE":
            ns = by_sec[sec]; cnt = sum(len(STEPS[n]["ids"]) for n in ns)
            c.setFillColor(ACCENT); c.circle(M + 9, y + 3, 9, stroke=0, fill=1)
            c.setFillColor(INK); c.setFont("DVB", 10); c.drawCentredString(M + 9, y - 0.5, sec)
            c.setFont("DVB", 10); c.drawString(M + 26, y + 2, SEC_INFO[sec][0])
            c.setFont("DV", 8.5); c.setFillColor(MUTED)
            c.drawString(M + 26, y - 10, f"Schritte {ns[0] + 1}–{ns[-1] + 1} · {cnt:,} Teile · ab Seite {sec_first_page[sec]}".replace(",", "."))
            y -= 34
        c.setFillColor(INK); c.setFont("DV", 8.5); c.drawString(M + 26, y + 2, f"Stückliste: ab Seite {bom_first}")
        y -= 26
        c.setFont("DVB", 12); c.drawString(M, y, "So liest du die Anleitung"); y -= 16
        for t in ["Neue Teile eines Schritts sind farbig, bereits verbaute Teile blass dargestellt.",
                  "Der graue Kasten zeigt alle Teile des Schritts mit Anzahl.",
                  "Gelbe Kästen mit ! sind Arbeitsschritte ohne Steine (LEDs, Kabel, Montage) – nicht überspringen.",
                  "Vorne ist die Seite, auf der Afrika auf der Kuppel zu sehen ist; das Mosaik ist von dort lesbar.",
                  "Die großen Lagen sind in Viertel oder Achtel aufgeteilt: einmal im Kreis herum bauen."]:
            y = para(c, "• " + t, M, y, colw, size=9) - 3
        x2 = M + colw + 30; y = H - M - 56
        c.setFont("DVB", 12); c.setFillColor(INK); c.drawString(x2, y, "Außer LEGO brauchst du"); y -= 16
        for t in ["LED-Streifen 5 mm COB, 5 V (USB), ca. 1,2 m – kalt- oder neutralweiß",
                  "24 kleine LEDs mit dünnen Drähten (z. B. Dot Lights eines LEGO-Beleuchtungssets) + Verteiler-Platinen",
                  "USB-Netzteil 5 V (mind. 2 A) und ein USB-Y-Kabel",
                  f"4 Hilfsstützen, je {D['sup_h'] * 0.4:.0f} mm hoch (Bücher, Kartons oder gestapelte Steine)",
                  "2 Bücherstapel o. Ä. zum Aufbocken des Truss-Rings",
                  "Eine zweite Person zum Aufsetzen des Dachs (48 × 48 cm, ca. 1,4 kg)"]:
            y = para(c, "• " + t, x2, y, colw, size=9) - 3
        y -= 10
        c.setFont("DVB", 12); c.drawString(x2, y, "Tipps"); y -= 16
        for t in ["Teile vor dem Bauen nach Farbe und Größe sortieren – allein 3.600 Fliesen gehen ins Mosaik.",
                  "Die Kuppel ist innen hohl: Innenstützen immer mit der Lage bauen, in der sie im Bild erscheinen.",
                  "Truss-Ring und Dach sind Baugruppen, die separat gebaut und erst in Abschnitt E eingesetzt werden.",
                  "Kabel-Schritte vor dem Schließen der jeweiligen Lage erledigen – nachträglich kommt man nicht mehr hin."]:
            y = para(c, "• " + t, x2, y, colw, size=9) - 3
        footer(c, pno)
    elif typ == "pruefung":
        c.setFillColor(INK); c.setFont("DVB", 20); c.drawString(M, H - M - 20, "Prüfung der Bauschritte")
        y = para(c, "Jeder Schritt dieser Anleitung wurde vor dem Erstellen automatisch gegen das Modell geprüft "
                    "(Skript globe-stage/anleitung/plan_steps.py). Geprüft wird mit der tatsächlichen Noppen-Geometrie aller Teile:",
                 M, H - M - 46, W - 2 * M, size=9.5)
        y -= 6
        rows = [("Vollständigkeit", "Jedes der %s Teile kommt genau einmal in einem Schritt vor." % f"{n_parts:,}".replace(",", ".")),
                ("Verbindung", "Nach jedem Schritt hängt alles Gebaute zusammen – das Hauptmodell an den Grundplatten, "
                               "Truss-Ring und Dach jeweils in sich. Es gibt keinen Zwischenstand mit losen Teilen."),
                ("Einsetzbarkeit", "Jedes Teil lässt sich von oben aufstecken, weil über ihm noch nichts verbaut ist. "
                                   "Nur Teile an Unterseiten (Scheinwerfer, Clips, Seile) werden von unten eingesteckt – dort ist Platz."),
                ("Endmontage", "Ring passt zwischen den Türmen durch, hängt frei über der Kuppel, Dach lässt sich aufsetzen, "
                               "Seil-Enden sind erreichbar, Hilfsstützen stehen eben und nicht unter Lampen oder Seilen."),
                ("Modell", "Keine Kollisionen, keine schwebenden Teile, Kabelwege frei, Statik-Abschätzung OK.")]
        for t, d in rows:
            c.setFillColor(OKG); c.setFont("DVB", 12); c.drawString(M, y - 2, "✓")
            c.setFillColor(INK); c.setFont("DVB", 10); c.drawString(M + 18, y, t)
            y = para(c, d, M + 120, y, W - 2 * M - 120, size=9) - 6
        y -= 6
        c.setFont("DVB", 11); c.setFillColor(INK); c.drawString(M, y, "Prüfprotokoll"); y -= 14
        c.setFont("DV", 8); c.setFillColor(MUTED)
        for ln in D["report"]:
            c.drawString(M, y, ln[:170]); y -= 10.5
        y -= 8
        y = para(c, "Durch diese Prüfung gefunden und im Modell behoben: Die zwei Bodenplatten-Lagen des Truss-Rings lagen "
                    "teilweise parallel und hielten ohne die Wände nicht zusammen (der Ring wäre beim Bauen in 15 Stücke "
                    "zerfallen). Die obere Lage wird jetzt gezielt so gelegt, dass sie alle Platten der unteren Lage zu einem "
                    "Stück verbindet.", M, y, W - 2 * M, size=9, color=INK)
        footer(c, pno)
    elif typ == "abschnitt":
        sec = dat; ns = by_sec[sec]
        c.setFillColor(INK); c.rect(0, H - 150, W, 150, stroke=0, fill=1)
        c.setFillColor(ACCENT); c.circle(M + 40, H - 75, 36, stroke=0, fill=1)
        c.setFillColor(INK); c.setFont("DVB", 40); c.drawCentredString(M + 40, H - 89, sec)
        c.setFillColor(white); c.setFont("DVB", 26); c.drawString(M + 96, H - 70, SEC_INFO[sec][0])
        cnt = sum(len(STEPS[n]["ids"]) for n in ns)
        c.setFont("DV", 11); c.setFillColor(HexColor("#AEB8C0"))
        c.drawString(M + 96, H - 94, f"Schritte {ns[0] + 1}–{ns[-1] + 1} · {cnt:,} Teile".replace(",", "."))
        para(c, SEC_INFO[sec][1], M + 96, H - 116, W - M - 96 - M, size=10, color=white)
        draw_img(c, shot(f"sec_{sec}"), M, 40, W - 2 * M, H - 150 - 60, trim=True, maxw=1100)
        footer(c, pno, sec)
    elif typ in ("zwei", "eins"):
        ids = dat if typ == "zwei" else (dat,)
        sec = STEPS[ids[0]]["sec"]
        colw = (W - 2 * M - 24) / 2 if typ == "zwei" else W - 2 * M
        for k, n in enumerate(ids):
            x = M + k * (colw + 24)
            draw_step(c, n, STEPS[n], x, H - M, colw, H - M - 32)
        if typ == "zwei":
            c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(W / 2, H - M, W / 2, 34)
        footer(c, pno, sec)
    elif typ == "mosaik_gesamt":
        c.setFillColor(INK); c.setFont("DVB", 20); c.drawString(M, H - M - 20, "Dach-Mosaik: Gesamtplan 60 × 60")
        size = H - M - 60 - 40
        cs = size / 60; x0 = M; y0 = H - M - 46
        for r in range(60):
            for q in range(60):
                c.setFillColor(HexColor(MCOL[MOSAIC[r][q]][1])); c.setStrokeColor(HexColor("#B8C0C6")); c.setLineWidth(0.15)
                c.rect(x0 + q * cs, y0 - (r + 1) * cs, cs, cs, stroke=1, fill=1)
        c.setStrokeColor(INK); c.setLineWidth(0.6)
        for k in range(0, 61, 10):
            c.line(x0 + k * cs, y0, x0 + k * cs, y0 - 60 * cs); c.line(x0, y0 - k * cs, x0 + 60 * cs, y0 - k * cs)
        c.setFont("DV", 7); c.setFillColor(MUTED)
        for k in range(0, 60, 10):
            c.drawRightString(x0 - 3, y0 - (k + 0.7) * cs, str(k + 1))
        c.setFont("DVB", 8); c.setFillColor(INK)
        c.drawCentredString(x0 + 30 * cs, y0 - 60 * cs - 12, "▼ VORNE (Publikumsseite) ▼")
        c.drawCentredString(x0 + 30 * cs, y0 + 4, "hinten")
        x = x0 + 60 * cs + 30; wtxt = W - M - x
        y = para(c, "Das Cover wird aus 3.600 Fliesen 1×1 in vier Grautönen gelegt – genau die Fläche innerhalb der Attika. "
                    "Lege das Dach so vor dich, dass die Vorderkante zu dir zeigt: Reihe 1 liegt hinten, Reihe 60 vorne, "
                    "Spalte 1 links. Gebaut wird in sechs Streifen zu je 10 Reihen.", x, H - M - 56, wtxt, size=9.5)
        y -= 8
        cnt = Counter("".join(MOSAIC))
        for ch in "KDLW":
            nm, fill, txt = MCOL[ch]
            c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor("#9AA3AA")); c.rect(x, y - 12, 16, 16, stroke=1, fill=1)
            c.setFillColor(HexColor(txt)); c.setFont("DVB", 8); c.drawCentredString(x + 8, y - 7, ch)
            c.setFillColor(INK); c.setFont("DV", 9.5); c.drawString(x + 24, y - 7, f"{nm}: {cnt[ch]:,} Fliesen".replace(",", "."))
            y -= 24
        y -= 6
        para(c, "Tipp: Einen Streifen immer Reihe für Reihe von links nach rechts legen und nach jeder fünften Spalte "
                "kurz mit dem Plan vergleichen – die dicken Linien im Plan helfen beim Abzählen.", x, y, wtxt, size=9, color=MUTED)
        footer(c, pno, "D")
    elif typ == "mosaik":
        n = dat; st = STEPS[n]; r0, r1 = st["chart"]
        c.setFillColor(INK); c.setFont("DVB", 26); c.drawString(M, H - M - 24, str(n + 1))
        c.setFont("DV", 9.5); c.setFillColor(MUTED); c.drawString(M + pdfmetrics.stringWidth(str(n + 1), "DVB", 26) + 10, H - M - 13, st["title"])
        hgt = mosaic_chart(c, r0, r1, M, H - M - 40, W - 2 * M)
        y = H - M - 40 - hgt - 14
        draw_img(c, shot(f"s{n + 1:03d}"), M, 34, 330, y - 34, trim=True, maxw=700)
        x = M + 350
        cnt = Counter(MOSAIC[r][q] for r in range(r0, r1) for q in range(60))
        c.setFont("DVB", 10); c.setFillColor(INK); c.drawString(x, y - 6, f"Fliesen 1×1 für die Reihen {r0 + 1}–{r1}:")
        yy = y - 26
        for ch in "KDLW":
            if not cnt[ch]: continue
            nm, fill, txt = MCOL[ch]
            p = thumb_path("3070b", {"K": 0, "D": 72, "L": 71, "W": 15}[ch])
            if os.path.exists(p): draw_img(c, p, x, yy - 18, 30, 30, trim=True)
            c.setFillColor(INK); c.setFont("DVB", 10); c.drawString(x + 40, yy - 6, f"{cnt[ch]}×")
            c.setFont("DV", 9); c.setFillColor(MUTED); c.drawString(x + 80, yy - 6, f"{nm} ({ch})")
            yy -= 36
        para(c, "Reihe 1 liegt hinten. Der Streifen im Bild links zeigt, wo die Reihen dieses Schritts auf dem Dach liegen.",
             x, yy - 6, W - M - x, size=8.5, color=MUTED)
        footer(c, pno, "D")
    elif typ == "fertig":
        c.setFillColor(INK); c.setFont("DVB", 22); c.drawString(M, H - M - 22, "Fertig!")
        c.setFont("DV", 10); c.setFillColor(MUTED)
        c.drawString(M, H - M - 40, "USB-Netzteil einstecken – LED-Ring und Scheinwerfer leuchten.")
        draw_img(c, shot("cover"), M, 34, W - 2 * M, H - M - 60 - 34, trim=True, maxw=1400)
        footer(c, pno)
    elif typ == "stueckliste":
        k0 = dat
        c.setFillColor(INK); c.setFont("DVB", 20)
        c.drawString(M, H - M - 20, "Stückliste" + ("" if k0 == 0 else " (Fortsetzung)"))
        c.setFont("DV", 8.5); c.setFillColor(MUTED)
        c.drawRightString(W - M, H - M - 18, f"{len(BOM)} Positionen · {n_parts:,} Teile · BrickLink-Liste: globe_stage_bricklink.xml".replace(",", "."))
        cols, rows_ = 8, 5
        cw = (W - 2 * M) / cols; ch_ = (H - M - 40 - 34) / rows_
        for k, ((nm, col), q) in enumerate(BOM[k0:k0 + PER]):
            r, cc = divmod(k, cols)
            x = M + cc * cw; y = H - M - 40 - (r + 1) * ch_
            c.setStrokeColor(LINE); c.setLineWidth(0.4); c.rect(x + 2, y + 2, cw - 4, ch_ - 4, stroke=1, fill=0)
            p = thumb_path(nm, col)
            if os.path.exists(p): draw_img(c, p, x + 6, y + 34, cw - 12, ch_ - 42, trim=True, maxw=240)
            c.setFillColor(INK); c.setFont("DVB", 10); c.drawString(x + 7, y + 22, f"{q}×")
            bl = NAMES.get(nm, (nm, nm))[1]
            c.setFont("DV", 6.5); c.setFillColor(MUTED)
            c.drawRightString(x + cw - 7, y + 22, bl)
            c.drawString(x + 7, y + 13, COLORS[col][0][:26])
            c.drawString(x + 7, y + 5.5, NAMES.get(nm, (nm, nm))[0][:34])
        footer(c, pno)
    c.showPage()
c.save()
print("PDF:", OUTPDF, "Seiten:", TOTAL)
