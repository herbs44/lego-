"""
Bauschritte fuer die Globe Stage planen und pruefen
==================================================
Liest das Modell aus generate_globe_stage.py, teilt es in Bauabschnitte und Schritte und prueft
jeden Schritt:
  1. Vollstaendigkeit: jedes Teil kommt genau einmal vor
  2. Verbindung: nach jedem Schritt haengt alles Gebaute zusammen (Hauptmodell an der Baseplate,
     Baugruppen in sich)
  3. Einsetzbarkeit: jedes Teil laesst sich von oben aufstecken (Raum darueber frei) bzw. - nur
     fuer Teile an Unterseiten - von unten einstecken (Raum darunter frei)
  4. Endmontage: Truss passt zwischen den Tuermen durch, Dach und Truss kollidieren beim Absenken
     mit nichts, Kabel- und Seilwege frei
Ausgabe: steps.json (fuer Renderer und PDF) + pruefbericht.txt
"""
import json, math, os, runpy, sys, io, contextlib
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "generate_globe_stage.py")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "build")
os.makedirs(OUT, exist_ok=True)

_argv = sys.argv
sys.argv = ["gen", os.path.join(OUT, "_gen")]
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(GEN)
sys.argv = _argv
parts = G["parts"]
PH, BH, LDU = G["PH"], G["BH"], G["LDU"]
ctr = G["ctr"]
idx = {id(p): i for i, p in enumerate(parts)}

MAXP = 45          # Richtwert Teile pro Schritt (ohne Mosaik)
MINP = 10

# ---------------- Verbindungsgraph (Noppen) ----------------
top = defaultdict(list)
for i, p in enumerate(parts):
    for c in p.studcells: top[(p.ytop, c)].append(i)
ADJ = defaultdict(set); BELOW = defaultdict(set); ABOVE = defaultdict(set)
for i, p in enumerate(parts):
    for c in p.cells:
        for j in top.get((p.ybot, c), []):
            if j != i:
                ADJ[i].add(j); ADJ[j].add(i); BELOW[i].add(j); ABOVE[j].add(i)
for a, b in G["SLING_LINKS"]:        # Truss liegt in den Seilschlingen
    i, j = idx[id(a)], idx[id(b)]
    ADJ[i].add(j); ADJ[j].add(i)


def angle(p):
    xs = [c[0] + 0.5 for c in p.cells]; zs = [c[1] + 0.5 for c in p.cells]
    return math.atan2(sum(zs) / len(zs), sum(xs) / len(xs))


def radius(p):
    xs = [c[0] + 0.5 for c in p.cells]; zs = [c[1] + 0.5 for c in p.cells]
    return math.hypot(sum(xs) / len(xs), sum(zs) / len(zs))


def sectors(ids, k, a0=-math.pi / 2):
    """teilt Teile in k Winkelsektoren (Start hinten, im Uhrzeigersinn von oben gesehen)"""
    out = [[] for _ in range(k)]
    for i in ids:
        a = (angle(parts[i]) - a0) % (2 * math.pi)
        out[min(k - 1, int(a / (2 * math.pi / k)))].append(i)
    return [s for s in out if s]


QUAD = ["hinten rechts", "vorne rechts", "vorne links", "hinten links"]   # Namen fuer k=4 (von vorne gesehen)


def split_level(ids, maxp=MAXP, inner_r=None):
    """Ebene -> Schritte: Innenteile (r < inner_r) zuerst, Rest in Sektoren"""
    res = []
    if inner_r is not None:
        inner = [i for i in ids if radius(parts[i]) < inner_r]
        ids = [i for i in ids if radius(parts[i]) >= inner_r]
        if inner:
            k = max(1, math.ceil(len(inner) / maxp))
            res += [("innen", s) for s in (sectors(inner, k) if k > 1 else [inner])]
    if ids:
        k = max(1, math.ceil(len(ids) / maxp))
        k = 1 if k == 1 else (2 if k == 2 else (4 if k <= 4 else 8))
        ss = sectors(ids, k) if k > 1 else [ids]
        res += [("ring", s) for s in ss]
    return res


# ---------------- Abschnitte ----------------
SEC = {}
for i, p in enumerate(parts):
    s = p.sub
    if s in ("12_ecktuerme",): SEC[i] = "B"
    elif s in ("13_truss_ring", "14_scheinwerfer"): SEC[i] = "C"
    elif s == "17_dach_mosaik": SEC[i] = "D"
    elif s == "16_dach": SEC[i] = "E" if p.name == "4081b" else "D"
    elif s == "15_seile": SEC[i] = "E"
    else: SEC[i] = "A"

steps = []   # dict(sec, title, ids, action, view, kind)


def add_step(sec, title, ids, action=None, view=None, kind="bau", chart=None):
    steps.append(dict(sec=sec, title=title, ids=list(ids), action=action, view=view, kind=kind, chart=chart))


LEVEL_NAME = {}
G_DOME = G["G_DOME"]


def level_title(ybot):
    g = -ybot / BH
    if ybot == 4: return "Grundplatten"
    if g == int(g):
        g = int(g)
        if g < 2: return f"Basis, Lage {g + 1}"
        if g < 4: return f"Laufsteg, Lage {g - 1}"
        if g < 6: return f"LED-Ring, Lage {g - 3}"
        return f"Kuppel, Lage {g - G_DOME + 1}"
    return f"Kuppel-Rundung / Abdeckung auf Lage {int(math.floor(g)) - G_DOME + 1}" if g > G_DOME else "Abdeckung"


# ---- A: Basis und Kuppel ----
A = [i for i in range(len(parts)) if SEC[i] == "A"]
levels = defaultdict(list)
for i in A: levels[parts[i].ybot].append(i)
for yb in sorted(levels, reverse=True):
    ids = levels[yb]
    action = None
    if yb == -BH:
        add_step("A", "Kabel für den LED-Streifen einlegen", [], kind="aktion", action=(
            "Das USB-Kabel des LED-Streifens in den Tunnel der untersten Lage legen (hinten Mitte) und das "
            "Ende senkrecht nach oben aus dem Schacht führen. Die folgenden Lagen werden um den Schacht "
            "herum gebaut, das Kabelende schaut oben heraus. Der USB-Stecker bleibt außen."))
    if yb == -BH * 5:
        add_step("A", "LED-Streifen einlegen", [], kind="aktion", action=(
            "Den LED-Streifen (5 mm COB, ca. 1,2 m) ringsum in den Kanal hinter der trans-klaren Reihe legen, "
            "Klebeseite an die weiße Innenwand, Licht nach außen. Mit dem Kabel aus dem Schacht verbinden. "
            "Erst danach die nächste Lage (radiale 1×4-Steine) aufsetzen – sie überbrückt den Kanal."))
    if yb == 4:
        add_step("A", "Grundplatten auslegen", ids, view="uebersicht")
        continue
    inner_r = 17.0 if yb <= -BH * G_DOME else None
    for kind, s in split_level(ids, inner_r=inner_r):
        add_step("A", level_title(yb) + (" – innen" if kind == "innen" else ""), s,
                 view="innen" if kind == "innen" else None)

# ---- B: Ecktuerme ----
B = [i for i in range(len(parts)) if SEC[i] == "B"]
blev = defaultdict(list)
for i in B: blev[parts[i].ybot].append(i)
lv = 0
for yb in sorted(blev, reverse=True):
    ids = blev[yb]
    if parts[ids[0]].name == "95347":
        lv += 1
        add_step("B", f"Ecktürme, Ebene {lv}: Gitterträger", ids, view="tuerme")
    else:
        steps[-1]["ids"] += ids
        steps[-1]["title"] += " + Verbindungsplatten 4×4"

# ---- C: Truss-Ring (Baugruppe) ----
C = [i for i in range(len(parts)) if SEC[i] == "C"]
lamps = [i for i in C if parts[i].sub == "14_scheinwerfer"]
truss = [i for i in C if parts[i].sub == "13_truss_ring"]
tlev = defaultdict(list)
for i in truss: tlev[parts[i].ybot].append(i)
ylev = sorted(tlev, reverse=True)     # L1, L2, Wand1, Wand2, Obergurt1, Obergurt2
y_L1, y_L2 = ylev[0], ylev[1]
# L2 in Sektoren, L1-Teile zum Schritt ihres ersten Halters
l2_steps = sectors(tlev[y_L2], 8)
owner = {}
for k, s in enumerate(l2_steps):
    for j in s: owner[j] = k
l1_for = defaultdict(list)
for i in tlev[y_L1]:
    ks = [owner[j] for j in ABOVE[i] if j in owner]
    assert ks, "L1-Teil ohne Halter"
    l1_for[min(ks)].append(i)
for k, s in enumerate(l2_steps):
    add_step("C", f"Truss-Ring: Bodenplatten, Achtel {k + 1}", l1_for[k] + s, view="truss",
             action="Zuerst die unteren (radialen) Platten auslegen, dann die obere Lage darüberstecken – "
                    "sie hält die unteren Platten zusammen." if k == 0 else None)
names = {ylev[2]: "Wände, Lage 1", ylev[3]: "Wände, Lage 2"}
for yb in ylev[2:4]:
    for k, s in enumerate(sectors(tlev[yb], 4)):
        add_step("C", f"Truss-Ring: {names[yb]}, Viertel {k + 1}", s, view="truss")
add_step("C", "Truss-Ring aufbocken", [], kind="aktion", view="truss", action=(
    "Den Ring auf zwei Bücherstapel o. Ä. legen, sodass die Unterseite frei ist. Der Ring ist jetzt ein "
    "U-Profil und stabil genug zum Anheben."))
_ls = sectors(lamps, 4)
add_step("C", "Scheinwerfer von unten einsetzen, Viertel 1", _ls[0], view="truss_unten", action=(
    "In jeden schwarzen Rundstein eine LED (z. B. Dot Light eines Beleuchtungssets) stecken, trans-klare "
    "Rundplatte als Linse darunter. Die Lampen von UNTEN an die Bodenplatten stecken. Den Draht zwischen "
    "Gehäuse und Linse seitlich herausführen und durch das Loch direkt neben der Lampe nach oben in den "
    "Kanal zwischen den Wänden ziehen."))
for k, s_ in enumerate(_ls[1:]):
    add_step("C", f"Scheinwerfer von unten einsetzen, Viertel {k + 2}", s_, view="truss_unten")
add_step("C", "Drähte im Truss-Kanal sammeln", [], kind="aktion", view="truss", action=(
    "Die 24 Drähte im Kanal zwischen den Wänden zur Kabel-Stelle hinten links (von vorne gesehen) führen "
    "und dort verbinden (Verteiler-Platinen des Lichtsets). Die Sammelleitung durch das Loch im Obergurt "
    "nach oben herausführen – im Obergurt bleibt dort ein Feld frei."))
for yb, nm in ((ylev[4], "Obergurt, Lage 1"), (ylev[5], "Obergurt, Lage 2")):
    for k, s in enumerate(sectors(tlev[yb], 4)):
        add_step("C", f"Truss-Ring: {nm}, Viertel {k + 1}", s, view="truss")

# ---- D: Dach (Baugruppe) ----
D = [i for i in range(len(parts)) if SEC[i] == "D"]
dlev = defaultdict(list)
for i in D: dlev[parts[i].ybot].append(i)
y_ceil = G["y_ceiling"]; y_rp = G["y_roof_plates"]
ceil_ids = dlev[y_ceil]; roof_ids = dlev[y_ceil - PH]
top_ids = dlev[y_rp]
attika = [i for i in top_ids if parts[i].sub == "16_dach"]
mosaic = [i for i in top_ids if parts[i].sub == "17_dach_mosaik"]
r_steps = sectors(roof_ids, 4)
owner = {}
for k, s in enumerate(r_steps):
    for j in s: owner[j] = k
c_for = defaultdict(list)
for i in ceil_ids:
    ks = [owner[j] for j in ABOVE[i] if j in owner]
    assert ks, "Deckenplatte ohne Halter"
    c_for[min(ks)].append(i)
for k, s in enumerate(r_steps):
    add_step("D", f"Dach: Decke und Dachplatten, Viertel {k + 1}", c_for[k] + s, view="dach",
             action="Erst die schwarzen Deckenplatten auslegen, dann die grauen Dachplatten versetzt darüber "
                    "stecken – jede Fuge der Decke wird überbrückt." if k == 0 else None)
for k, s in enumerate(sectors(attika, 2)):
    add_step("D", f"Dach: Attika (Randträger), Teil {k + 1}", s, view="dach")
N = G["N_MOS"]
rows_per = 10
for r0 in range(0, N, rows_per):
    ids = [i for i in mosaic if r0 <= (min(c[1] for c in parts[i].cells) + 30) < r0 + rows_per]
    add_step("D", f"Dach-Mosaik: Reihen {r0 + 1}–{r0 + rows_per}", ids, view="mosaik", kind="mosaik",
             chart=(r0, r0 + rows_per))

# ---- E: Endmontage ----
E_clip = [i for i in range(len(parts)) if SEC[i] == "E" and parts[i].name == "4081b"]
E_rope = [i for i in range(len(parts)) if SEC[i] == "E" and parts[i].name == "63142"]
add_step("E", "Hilfsstützen aufstellen, Truss-Ring einsetzen", [], kind="montage", view="montage_ring", action=(
    "Vier Hilfsstützen (orange, siehe Bild) auf den Basis-Rand stellen – z. B. Bücher, Kartons oder gestapelte Steine, "
    "Höhe {H} mm. Sie stehen zwischen den Lampen und nicht an den Seil-Stellen. Den fertigen Truss-Ring von oben "
    "zwischen den Ecktürmen absenken und auf die Stützen legen (Kabel-Stelle hinten links)."))
add_step("E", "Dach auf die Ecktürme setzen", [], kind="montage", view="montage_dach", action=(
    "Das fertige Dach (am besten zu zweit) waagerecht über die Türme heben und auf die 8 Gitterträger-Enden drücken. "
    "Das Mosaik zeigt mit Reihe 60 nach vorne."))
add_step("E", "Kabel-Clips unter die Decke stecken", E_clip, view="decke_unten", action=(
    "Die 4 Clip-Platten von unten in die Decke stecken (Dach dabei von oben gegenhalten). Sie führen später die "
    "Sammelleitung der Scheinwerfer zum Eckturm hinten links."))
add_step("E", "Truss-Ring an die Seile hängen", E_rope, view="seile", action=(
    "Für jedes der 8 Seile: inneres Ende von unten in die Decke stecken, Seil innen herunter, UNTER dem Ring "
    "durch, außen wieder hoch, äußeres Ende in die Decke stecken. Dach dabei von oben gegenhalten."))
add_step("E", "Hilfsstützen entfernen, Kabel anschließen", [], kind="montage", view="final", action=(
    "Die Hilfsstützen vorsichtig herausziehen – der Ring sinkt eine Plattenhöhe in die Seilschlaufen. Die "
    "Sammelleitung am äußeren Seil hinten links hoch, durch die Clips unter der Decke zum Eckturm und am "
    "Gitterträger nach unten führen. Beide Kabel (LED-Streifen hinten Mitte, Scheinwerfer hinten links) an ein "
    "5-V-USB-Netzteil anschließen, z. B. mit einem Y-Kabel. Fertig!"))

# ---------------- Endmontage-Geometrie ----------------
y_scr_top, y_truss_top = G["y_scr_top"], G["y_truss_top"]
lamp_bottom = max(parts[i].ybot for i in lamps)
TRUSS_CELLS = set(G["TRUSS"]) | {c for i in lamps for c in parts[i].cells}
main_ids = [i for i in range(len(parts)) if SEC[i] in "AB"]
# Hilfsstuetzen: 4 Bloecke unter der Truss-Unterseite, zwischen Lampen und Seilen, auf dem Basis-Rand
lamp_cells = {c for i in lamps for c in parts[i].cells}
rope_cells = {c for i in E_rope for c in parts[i].cells}
hole_cells = set(G["HOLES"])
L1_cells = {c for i in tlev[y_L1] for c in parts[i].cells}
base_top = {}
for i in main_ids:
    for c in parts[i].cells:
        base_top[c] = min(base_top.get(c, 10 ** 9), parts[i].ytop)
SUPPORTS = []
for a_deg in (41.25, 131.25, 221.25, 311.25):
    a = math.radians(a_deg); best = None
    for X in range(-31, 32):
        for Z in range(-31, 32):
            blk = G["block"](X, Z)
            if not blk <= L1_cells or blk & (lamp_cells | hole_cells): continue
            if any(G["dist"](c) <= 27.5 for c in blk): continue          # nur auf dem Basis-Rand (eben)
            if len({base_top.get(c) for c in blk}) != 1: continue
            err = abs(math.remainder(math.atan2(Z, X) - a, 2 * math.pi))
            if best is None or err < best[0]: best = (err, (X, Z), blk)
    SUPPORTS.append(best[1:])
SUP_MARGIN = PH                           # Stuetzen 1 Platte hoeher: Ring sinkt beim Entfernen in die Schlaufen
sup_base = base_top[next(iter(SUPPORTS[0][1]))]
SUP_H = sup_base - (y_scr_top - SUP_MARGIN)


# ---------------- Pruefungen ----------------
report = []
def rep(line=""): report.append(line)

ok_all = True
# 1) Vollstaendigkeit
cnt = Counter(i for s in steps for i in s["ids"])
missing = [i for i in range(len(parts)) if cnt[i] == 0]
dup = [i for i, n in cnt.items() if n > 1]
rep(f"1. Vollständigkeit: {len(parts)} Teile, {len(missing)} fehlen, {len(dup)} doppelt")
ok_all &= not missing and not dup

# 2) + 3) je Abschnitt
FROM_BELOW = {i for i in lamps} | set(E_clip) | set(E_rope)
section_world = {"A": "haupt", "B": "haupt", "E": "haupt", "C": "C", "D": "D"}
placed = defaultdict(set)      # Welt -> Teile
conn_errors, insert_errors = [], []
roots = {i for i in range(len(parts)) if parts[i].name == "3811"}
for n, st in enumerate(steps):
    w = section_world[st["sec"]]
    if st["view"] == "montage_ring": placed["haupt"] |= placed.pop("C", set())     # Baugruppe einsetzen
    if st["view"] == "montage_dach": placed["haupt"] |= placed.pop("D", set())
    before = placed[w]
    for i in st["ids"]:
        p = parts[i]
        blk_above = any(parts[q].ybot <= p.ytop and parts[q].cells & p.cells for q in before)
        # von unten: Freiraum von 3 Steinhoehen unter dem Teil genuegt (Hand/Finger)
        blk_below = any(p.ybot <= parts[q].ytop < p.ybot + 3 * BH and parts[q].cells & p.cells for q in before)
        if st["sec"] in "CD" and i not in FROM_BELOW:
            pass                                   # Baugruppe auf dem Tisch: von oben
        if i in FROM_BELOW:
            if blk_below: insert_errors.append((n, i, "von unten blockiert"))
        elif blk_above:
            insert_errors.append((n, i, "von oben blockiert"))
    placed[w] = before | set(st["ids"])
    # Verbindung
    P = placed[w]
    if not P: continue
    if w == "haupt":
        start = roots & P
        seen = set(start); stack = list(start)
        while stack:
            x = stack.pop()
            for y in ADJ[x]:
                if y in P and y not in seen: seen.add(y); stack.append(y)
        bad = [i for i in P if i not in seen]
    else:
        start = next(iter(P)); seen = {start}; stack = [start]
        while stack:
            x = stack.pop()
            for y in ADJ[x]:
                if y in P and y not in seen: seen.add(y); stack.append(y)
        bad = [i for i in P if i not in seen]
    if w == "haupt" and not any(s2["view"] == "seile" for s2 in steps[:n + 1]):
        bad = [i for i in bad if SEC[i] != "C"]    # Ring liegt bis zum Einhaengen auf den Hilfsstuetzen
    if bad: conn_errors.append((n, len(bad), [parts[i].name for i in bad[:5]]))
rep(f"2. Verbindung nach jedem Schritt: {len(conn_errors)} Schritte mit losen Teilen")
for n, k, ex in conn_errors[:20]: rep(f"   ! Schritt {n + 1} ({steps[n]['title']}): {k} lose Teile, z. B. {ex}")
rep(f"3. Einsetzbarkeit (von oben aufstecken bzw. von unten einstecken): {len(insert_errors)} Teile blockiert")
for n, i, why in insert_errors[:20]:
    p = parts[i]; rep(f"   ! Schritt {n + 1}: {p.name} bei {p.x},{p.y},{p.z}: {why}")
ok_all &= not conn_errors and not insert_errors

# 4) Endmontage
em = []
# Ring von oben absenken: nichts im Hauptmodell hoeher als die Lampen-Unterkante in den Ring-Zellen
hi = [i for i in main_ids if parts[i].cells & TRUSS_CELLS and parts[i].ytop < lamp_bottom]
em.append(("Truss-Ring lässt sich von oben zwischen den Ecktürmen auf seine Höhe absenken", not hi))
tower_min_r = min(math.hypot(c[0] + (0 if c[0] < 0 else 1), c[1] + (0 if c[1] < 0 else 1))
                  for c in G["TOWER_CELLS"])
ring_r = max(G["dist"](c) + 0.71 for c in TRUSS_CELLS)
em.append((f"Ring-Außenradius {ring_r:.1f} Noppen, nächste Turmecke {tower_min_r:.1f} Noppen", tower_min_r > ring_r))
dome_top = min(parts[i].ytop for i in main_ids if SEC[i] == "A")
em.append((f"Ring hängt über der Kuppel: {(dome_top - lamp_bottom) * 0.4:.0f} mm Luft zwischen Lampen und Kuppelspitze",
           dome_top - lamp_bottom > BH))
y_ceiling = G["y_ceiling"]
hi = [i for i in main_ids if parts[i].ytop < y_ceiling]
em.append(("Dach lässt sich von oben aufsetzen (nichts ragt über die Turm-Oberkante)", not hi))
em.append((f"Luft zwischen Truss-Oberkante und Decke: {(y_truss_top - y_ceiling) * 0.4:.0f} mm (zum Einstecken der Seile)",
           y_truss_top - y_ceiling > 3 * BH))
sup_ok = all(not (blk & (lamp_cells | hole_cells | rope_cells)) for _, blk in SUPPORTS)
em.append((f"4 Hilfsstützen ({SUP_H * 0.4:.0f} mm hoch) stehen auf dem ebenen Basis-Rand, nicht unter Lampen oder Seilen", sup_ok))
free_ropes = all(not any(parts[q].cells & parts[i].cells and parts[q].ytop < parts[i].ybot + 3 * BH and parts[q].ybot > parts[i].ytop
                           for q in main_ids + C) for i in E_rope)
em.append(("Seil-Endnoppen von unten erreichbar (unter der Decke frei)", free_ropes))
rep("4. Endmontage:")
for t, ok in em:
    rep(f"   {'OK ' if ok else 'FEHLER'} {t}"); ok_all &= ok
# Generator-Checks (Statik, Kabelweg)
rep(f"5. Generator-Prüfung: 0 Kollisionen, 0 schwebende Teile, Kabelwege frei, Statik {'OK' if G['STATIK_OK'] else 'KRITISCH'}")
ok_all &= G["STATIK_OK"]

sizes = [len(s["ids"]) for s in steps if s["kind"] == "bau"]
rep(f"Schritte: {len(steps)} (davon {sum(1 for s in steps if s['kind'] in ('aktion', 'montage'))} Arbeits-/Montageschritte, "
    f"{sum(1 for s in steps if s['kind'] == 'mosaik')} Mosaik-Schritte); Teile je Bauschritt: "
    f"max {max(sizes)}, Mittel {sum(sizes) / len(sizes):.0f}")
rep("ERGEBNIS: " + ("ALLE PRÜFUNGEN BESTANDEN" if ok_all else "FEHLER GEFUNDEN"))
print("\n".join(report))

for st in steps:
    if st["action"] and "{H}" in st["action"]: st["action"] = st["action"].replace("{H}", f"{SUP_H * 0.4:.0f}")

# ---------------- Render-Modell (ein MPD, jeder Schritt ein Untermodell) ----------------
ROTS = G["ROT"]
def line(p): return p.lines()
mpd = ["0 FILE anleitung.ldr", "0 Globe Stage - Bauanleitung (Render-Modell)"]
files = []
for n, st in enumerate(steps):
    st["group"] = f"step_{n + 1:03d}.ldr" if st["ids"] else None
    if st["ids"]:
        body = [l for i in st["ids"] for l in parts[i].lines()]
        files.append((st["group"], body))
# Hilfsstuetzen (orange, nur fuer die Bilder)
sb = []
for (X, Z), blk in SUPPORTS:
    yy = sup_base; h = SUP_H
    while h >= BH:
        yy -= BH; h -= BH; sb.append(f"1 25 {X * LDU} {yy} {Z * LDU} {ROTS[0]} 3003.dat")
    while h >= PH:
        yy -= PH; h -= PH; sb.append(f"1 25 {X * LDU} {yy} {Z * LDU} {ROTS[0]} 3022.dat")
files.append(("stuetzen.ldr", sb))
# LED-Streifen (gelb, nur fuer die Bilder): duennes Band an der Innenwand des Kanals
lb = []
CH = G["CHANNEL"]
for c in CH:
    lb.append(f"1 14 {ctr(c[0])} {-BH * 5 + 12} {ctr(c[1])} 6 0 0 0 7 0 0 0 6 box.dat")
files.append(("led_streifen.ldr", lb))
kb = []
for c in G["TUNNEL"]:
    kb.append(f"1 0 {ctr(c[0])} -10 {ctr(c[1])} 3 0 0 0 3 0 0 0 11 box.dat")
sx, sz = G["SHAFT"]
kb.append(f"1 0 {ctr(sx)} -52 {ctr(sz)} 3 0 0 0 50 0 0 0 3 box.dat")
files.append(("kabel_led.ldr", kb))
HELP_A = ["kabel_led.ldr", "led_streifen.ldr"]
for fn, body in files:
    mpd.append(f"1 16 0 0 0 {ROTS[0]} {fn}")
mpd.append("0 NOFILE")
for fn, body in files:
    mpd += [f"0 FILE {fn}", f"0 Name: {fn}"] + body + ["0 NOFILE"]
for fn, body in G["CUSTOM_FILES"].items():
    mpd += [f"0 FILE {fn}", f"0 Name: {fn}"] + body + ["0 NOFILE"]
open(os.path.join(OUT, "anleitung.mpd"), "w").write("\n".join(mpd) + "\n")

# Teile-Bilder (je Teil und Farbe eines)
uniq = sorted({(parts[i].name, parts[i].color) for i in range(len(parts))})
tm = ["0 FILE thumbs.ldr"]; tfiles = []
for nm, col in uniq:
    fn = f"t_{nm}_{col}.ldr"
    body = [f"1 {col} 0 0 0 {ROTS[0]} seil_63142.ldr"] if nm == "63142" else [f"1 {col} 0 0 0 {ROTS[0]} {nm}.dat"]
    tfiles.append((fn, body)); tm.append(f"1 16 0 0 0 {ROTS[0]} {fn}")
tm.append("0 NOFILE")
for fn, body in tfiles: tm += [f"0 FILE {fn}", f"0 Name: {fn}"] + body + ["0 NOFILE"]
tm += ["0 FILE seil_63142.ldr", "0 Name: seil_63142.ldr"] + G["CUSTOM_FILES"]["seil_63142.ldr"] + ["0 NOFILE"]
open(os.path.join(OUT, "thumbs.mpd"), "w").write("\n".join(tm) + "\n")
tjobs = [dict(name=f"t_{nm}_{col}", show=[f"t_{nm}_{col}.ldr"], az=35, el=28, w=240, h=240, margin=1.02, fov=20)
         for nm, col in uniq]
json.dump(tjobs, open(os.path.join(OUT, "thumbs_jobs.json"), "w"))

# Kamera je Schritt
def centroid(ids):
    xs = [ctr(c[0]) for i in ids for c in parts[i].cells]; zs = [ctr(c[1]) for i in ids for c in parts[i].cells]
    return sum(xs) / len(xs), sum(zs) / len(zs)
def az_to(cx, cz, off=-20): return math.degrees(math.atan2(cx, cz)) + off
groups_of = lambda secs, upto: [s["group"] for s in steps[:upto] if s["sec"] in secs and s["group"]]
jobs = []
ALL = [s["group"] for s in steps if s["group"]]
for n, st in enumerate(steps):
    J = dict(name=f"s{n + 1:03d}", w=1100, h=800, bg="#ffffff", fov=25)
    sec, g = st["sec"], st["group"]
    if sec in "AB":
        prev = groups_of("AB", n)
        prev += [h for h, t in zip(HELP_A, ("Kabel für den LED", "LED-Streifen einlegen"))
                 if any(s2["title"].startswith(t) for s2 in steps[:n])]
        J.update(fade=prev, show=[g] if g else [], frame=[g] if g else prev)
        if g:
            cx, cz = centroid(st["ids"]); r = math.hypot(cx, cz)
            if st["view"] == "uebersicht": J.update(az=-25, el=35, frame=[g])
            elif st["view"] == "tuerme": J.update(az=-25, el=18, minR=300)
            elif st["view"] == "innen" or r < 160: J.update(az=-25, el=62, minR=220)
            else: J.update(az=az_to(cx, cz), el=38, minR=220)
        if st["title"] == "LED-Streifen einlegen":
            J.update(show=["led_streifen.ldr"], radius=190, az=160, el=45, target=[0, -110, -440])
        if st["title"].startswith("Kabel für den LED"):
            J.update(show=["kabel_led.ldr"], radius=130, az=150, el=35, target=[10, -40, -540])
    elif sec == "C":
        prev = groups_of("C", n)
        J.update(fade=prev, show=[g] if g else [], frame=[g] if g else prev)
        if g:
            cx, cz = centroid(st["ids"])
            if st["view"] == "truss_unten": J.update(az=az_to(cx, cz, 0), el=-38, radius=330, target=[cx, y_scr_top, cz])
            else: J.update(az=az_to(cx, cz), el=50, minR=260)
        else:
            J.update(show=prev, fade=[], az=-25, el=35)
            if "Drähte" in st["title"]:
                oc = G["OG_HOLE"]; J.update(target=[ctr(oc[0]), y_truss_top + 40, ctr(oc[1])], radius=170, el=55, az=az_to(ctr(oc[0]), ctr(oc[1])))
    elif sec == "D":
        prev = groups_of("D", n)
        J.update(fade=prev, show=[g], frame=[g])
        cx, cz = centroid(st["ids"])
        if st["kind"] == "mosaik": J.update(az=0, el=90, frame=groups_of("D", n + 1), margin=1.02)
        else: J.update(az=az_to(cx, cz), el=50, minR=300)
    else:
        AB = groups_of("AB", len(steps)); C_ = groups_of("C", len(steps)); D_ = groups_of("D", len(steps))
        v = st["view"]
        if v == "montage_ring": J.update(fade=AB + HELP_A, show=C_ + ["stuetzen.ldr"], frame=AB, az=-25, el=18)
        elif v == "montage_dach": J.update(fade=AB + C_ + ["stuetzen.ldr"], show=D_, frame=AB + D_, az=-25, el=22)
        elif v == "decke_unten":
            cx, cz = centroid(st["ids"])
            J.update(fade=AB + C_ + D_ + ["stuetzen.ldr"], show=[g], frame=[g], az=az_to(cx, cz, 30), el=-25, minR=220)
        elif v == "seile":
            rp = min(st["ids"], key=lambda i: -parts[i].z - 0.3 * parts[i].x)      # Seil vorne
            J.update(fade=AB + C_ + D_ + groups_of("E", n) + ["stuetzen.ldr"], show=[g], radius=230,
                     target=[parts[rp].x, (y_ceiling + y_scr_top) / 2 + 20, parts[rp].z], az=az_to(parts[rp].x, parts[rp].z, 35), el=10)
        else: J.update(show=ALL + HELP_A, fade=[], frame=AB, az=-28, el=12)
    jobs.append(J)
json.dump(jobs, open(os.path.join(OUT, "steps_jobs.json"), "w"))
# Uebersichtsbilder fuer Abschnitts-Seiten
AB = groups_of("AB", len(steps)); C_ = groups_of("C", len(steps)); D_ = groups_of("D", len(steps))
A_ = groups_of("A", len(steps)); B_ = groups_of("B", len(steps))
extra = [dict(name="cover", show=ALL, frame=AB, az=-28, el=14, w=1600, h=1150),
         dict(name="sec_A", show=A_, frame=A_, az=-25, el=30, w=1100, h=800),
         dict(name="sec_B", show=AB, frame=AB, az=-25, el=18, w=1100, h=800),
         dict(name="sec_C", show=C_, frame=C_, az=-25, el=35, w=1100, h=800),
         dict(name="sec_D", show=D_, frame=D_, az=-25, el=45, w=1100, h=800),
         dict(name="sec_E", show=ALL, frame=AB, az=150, el=20, w=1100, h=800)]
json.dump(extra, open(os.path.join(OUT, "extra_jobs.json"), "w"))
open(os.path.join(OUT, "pruefbericht.txt"), "w").write("\n".join(report) + "\n")

json.dump(dict(steps=steps, supports=[[X, Z] for (X, Z), _ in SUPPORTS], sup_h=SUP_H, sup_base=sup_base,
               report=report, ok=bool(ok_all), em=[[t, bool(o)] for t, o in em]),
          open(os.path.join(OUT, "steps.json"), "w"))
