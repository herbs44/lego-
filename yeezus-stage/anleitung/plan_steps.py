"""
Bauschritte fuer die Yeezus Stage planen, pruefen und als Stud.io-Datei schreiben
================================================================================
Liest das Modell aus generate_yeezus_stage.py, teilt es in Bauabschnitte und Schritte und schreibt
yeezus_stage_anleitung.mpd mit "0 STEP"-Befehlen. Stud.io uebernimmt die Schritte beim Oeffnen in den
Instruction Maker; Traverse, Moving Head und Line-Array sind Untermodelle (Baugruppen).

Pruefungen je Schritt:
  1. Vollstaendigkeit: jedes Teil kommt genau einmal vor
  2. Verbindung: nach jedem Schritt haengt alles Gebaute zusammen (Hauptmodell an den Grundplatten,
     Baugruppen in sich)
  3. Einsetzbarkeit: jedes Teil laesst sich von oben aufstecken (Raum darueber frei), Gitter-Fliesen
     von der Seite, haengende Baugruppen von unten
  4. Endmontage: Traverse laesst sich von oben auf Tuerme und Screen absenken

Ausgabe: ../yeezus_stage_anleitung.mpd, schritte.txt (Titel und Hinweise je Schritt), pruefbericht.txt
Aufruf:  python yeezus-stage/anleitung/plan_steps.py
"""
import contextlib, io, math, os, runpy, sys, tempfile
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "generate_yeezus_stage.py")
OUT = os.path.join(HERE, "..")

sys.stdout.reconfigure(encoding="utf-8")
_argv = sys.argv
sys.argv = ["gen", tempfile.mkdtemp()]
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(GEN)
sys.argv = _argv
parts = G["parts"]
BH, PH, LDU, ROT, fmt = G["BH"], G["PH"], G["LDU"], G["ROT"], G["fmt"]
TRUSS_Y = G["TRUSS_Y"]
idx = {id(p): i for i, p in enumerate(parts)}
N = len(parts)

MAXP = 30          # Richtwert Teile pro Schritt

# ---------------- Verbindungsgraph (Noppen + SNOT) ----------------
top = defaultdict(list)
for i, p in enumerate(parts):
    for c in p.studcells: top[(p.ytop, c)].append(i)
ADJ = defaultdict(set); BELOW = defaultdict(set)
for i, p in enumerate(parts):
    for c in p.cells:
        for j in top.get((p.ybot, c), []):
            if j != i: ADJ[i].add(j); ADJ[j].add(i); BELOW[i].add(j)
SNOT = {}                                    # Gitter-Fliese -> Stein mit Seitennoppen
for a, b in G["SNOT_LINKS"]:
    i, j = idx[id(a)], idx[id(b)]
    ADJ[i].add(j); ADJ[j].add(i); SNOT[i] = j
ROOTS = {i for i, p in enumerate(parts) if p.name == "3811"}


def cxz(ids):
    xs = [(c[0] + 0.5) * LDU for i in ids for c in parts[i].cells]
    zs = [(c[1] + 0.5) * LDU for i in ids for c in parts[i].cells]
    return sum(xs) / len(xs), sum(zs) / len(zs)


def sectors(ids, k, center):
    """k zusammenhaengende Winkelsektoren mit gleich vielen Teilen, Start vorne (-x)"""
    cx, cz = center
    def ang(i):
        x, z = cxz([i]); return (math.atan2(z - cz, x - cx) - math.pi) % (2 * math.pi)
    s = sorted(ids, key=ang)
    return [s[round(n * len(s) / k):round((n + 1) * len(s) / k)] for n in range(k)]


def where(ids, center):
    """Lage eines Schritts von vorne gesehen (Publikum bei -x, +z = links)"""
    x, z = cxz(ids); dx, dz = x - center[0], z - center[1]
    t = 2 * LDU
    a = "vorne" if dx < -t else "hinten" if dx > t else ""
    b = "links" if dz > t else "rechts" if dz < -t else ""
    return " ".join(w for w in (a, b) if w) or "Mitte"


def layer(i):
    return math.floor(-parts[i].ybot / BH)


def layer_steps(ids, name, center, maxp=MAXP):
    """Teile nach Steinlagen; grosse Lagen in Sektoren, kleine aufeinanderfolgende Lagen zusammengefasst"""
    by = defaultdict(list)
    for i in ids: by[layer(i)].append(i)
    out, pend = [], None
    def flush():
        nonlocal pend
        if pend:
            g0, g1, s = pend
            lg = f"Lage {g0 + 1}" if g0 == g1 else f"Lagen {g0 + 1}–{g1 + 1}"
            out.append((f"{name}, {lg}", s)); pend = None
    for g in sorted(by):
        s = by[g]
        if len(s) > maxp:
            flush()
            k = math.ceil(len(s) / maxp)
            c = cxz(s) if center is None else center
            for ch in sectors(s, k, c):
                out.append((f"{name}, Lage {g + 1} – {where(ch, c)}", ch))
        elif pend and len(pend[2]) + len(s) <= maxp:
            pend = (pend[0], g, pend[2] + s)
        else:
            flush(); pend = (g, g, s)
    flush()
    return out


# ---------------- Abschnitte ----------------
SUB = defaultdict(list)
for i, p in enumerate(parts): SUB[p.sub].append(i)
TOWER = [i for i in SUB["08_traverse"] if parts[i].ybot > TRUSS_Y]
TRUSS = [i for i in SUB["08_traverse"] if parts[i].ybot <= TRUSS_Y]
MOUNTAIN = SUB["02_podest"] + SUB["03_berg"] + SUB["06_wendelweg"]

steps = []      # dict(model, title, ids, refs, note)


def add_step(model, title, ids=(), refs=(), note=None):
    steps.append(dict(model=model, title=title, ids=list(ids), refs=list(refs), note=note))


add_step("main", "Grundplatten auslegen", SUB["01_baseplates"],
         note="Zwei schwarze Grundplatten 32×32 nebeneinander, die lange Seite zeigt zum Publikum.")
for t, s in layer_steps(MOUNTAIN, "Mount Yeezus", None): add_step("main", t, s)
for t, s in layer_steps(SUB["04_laufsteg"], "Laufsteg mit Rampe", cxz(SUB["04_laufsteg"])): add_step("main", t, s)
for t, s in layer_steps(SUB["05_lower_stage"], "Center Stage (Keil)", cxz(SUB["05_lower_stage"])): add_step("main", t, s)
for t, s in layer_steps(SUB["07_screen"], "Runder Screen", cxz(SUB["07_screen"]), maxp=24): add_step("main", t, s)

# Ecktuerme: Sockel, dann je Ebene Gittertraeger + Verbindungsplatten
tl = defaultdict(list)
for i in TOWER: tl[parts[i].ybot].append(i)
cur, lv = [], 0
for yb in sorted(tl, reverse=True):
    ids = tl[yb]
    if parts[ids[0]].name == "95347" and cur:
        add_step("main", "Ecktürme: Sockel" if lv == 0 else f"Ecktürme: Gitterträger, Ebene {lv}", cur); cur = []; lv += 1
    cur += ids
add_step("main", f"Ecktürme: Gitterträger, Ebene {lv}", cur)

# ---- Baugruppe Traverse (auf dem Tisch) ----
TC = (0.0, -0.5 * LDU)
tv = defaultdict(list)
for i in TRUSS: tv[parts[i].ybot].append(i)
yl = sorted(tv, reverse=True)                # t1, t2, Saeulen 1, Saeulen 2, t3, t4
assert len(yl) == 6, yl
for (lo, hi), nm, nt in (((yl[0], yl[1]), "Traverse: untere Platten", (
        "Zuerst die unteren Platten auslegen, dann die zweite Lage versetzt darüberstecken – sie hält "
        "die unteren Platten zusammen.")),
        ((yl[4], yl[5]), "Traverse: obere Platten", None)):
    hs = sectors(tv[hi], 4, TC)
    owner = {j: k for k, s in enumerate(hs) for j in s}
    low = defaultdict(list)
    for i in tv[lo]:
        ks = [owner[j] for j in ADJ[i] if j in owner]
        low[min(ks) if ks else 0].append(i)
    for k, s in enumerate(hs):
        add_step("traverse", f"{nm} – {where(s, TC)}", low[k] + s, note=nt if k == 0 else None)
    if nm.startswith("Traverse: untere"):
        posts = tv[yl[2]] + tv[yl[3]]
        for k, s in enumerate(sectors(posts, 4, TC)):
            add_step("traverse", f"Traverse: Säulen (Rundsteine, 2 hoch) – {where(s, TC)}", s)


# ---- Baugruppen Moving Head (10x) und Line-Array (4x): lokale Koordinaten ----
def local_lines(ids, o):
    out = []
    for i in ids:
        for l in parts[i].lines():
            f = l.split()
            f[2], f[3], f[4] = fmt(float(f[2]) - o[0]), fmt(float(f[3]) - o[1]), fmt(float(f[4]) - o[2])
            out.append(" ".join(f))
    return out


def instances(ids, key, origin):
    grp = defaultdict(list)
    for i in ids: grp[key(i)].append(i)
    inst = [(k, sorted(v, key=lambda i: -parts[i].ybot), origin(k)) for k, v in sorted(grp.items())]
    ref = sorted(local_lines(inst[0][1], inst[0][2]))
    for _, v, o in inst:
        assert sorted(local_lines(v, o)) == ref, "Baugruppen nicht identisch"
    return inst


HEADS = instances(SUB["10_licht"], lambda i: (math.floor(parts[i].x / LDU), math.floor(parts[i].z / LDU)),
                  lambda k: (k[0] * LDU, TRUSS_Y, k[1] * LDU))
ARR = G["ARRAYS"]
def arr_of(i):
    c = next(iter(parts[i].cells))
    return next((ax, az) for ax, az in ARR if (c[1] >= 0) == (az >= 0) and ax - 8 <= c[0] <= ax)
ARRAYS = instances(SUB["09_line_arrays"], arr_of, lambda k: (k[0] * LDU, TRUSS_Y, k[1] * LDU))

add_step("moving_head", "Moving Head", HEADS[0][1],
         note=f"Rundplatte trans-klar, darauf Rundstein 2×2, oben Platte 2×2. {len(HEADS)}× bauen.")
a0 = ARRAYS[0][1]                             # unten beginnen: je Box 3 Teile + Platte darueber
units, cur = [], []
for i in a0:
    cur.append(i)
    if parts[i].name in ("3022", "3020"): units.append(cur); cur = []
assert not cur and len(units) == 13, len(units)
k = 4
for n in range(k):
    u = units[round(n * len(units) / k):round((n + 1) * len(units) / k)]
    add_step("line_array", f"Line-Array: Boxen {round(n * 13 / k) + 1}–{round((n + 1) * 13 / k)} (von unten)",
             [i for x in u for i in x],
             note="Box = Stein 1×2 mit Seitennoppen (vorne) + Stein 1×2, vorne eine Gitter-Fliese 1×2 auf die "
                  "Seitennoppen. Die Boxen versetzt mit Platten 2×2 stapeln, unten knickt das Array zum "
                  "Publikum ab (J-Form). 4× bauen." if n == 0 else None)

ref = lambda f, o: f"1 16 {fmt(o[0])} {fmt(o[1])} {fmt(o[2])} {ROT[0]} {f}"
if SUB.get("11_figuren"):
    add_step("main", "Figuren aufstellen (optional)", SUB["11_figuren"],
             note="Kanye (schwarz, Kopf in Flat Silver als Maske) auf die Spitze der Center Stage, Jesus auf den Gipfel, "
                  "die Tänzerinnen (weiß mit Kapuze) auf die Platten mit Noppen am Wendelweg. Figuren vorher "
                  "zusammenstecken: Beine, Torso, Kopf, Kapuze bzw. Haare und Bart.")
add_step("main", "Traverse auf die Ecktürme setzen", refs=[ref("traverse.ldr", (0, 0, 0))],
         note="Die fertige Traverse (am besten zu zweit) waagerecht von oben auf die sechs Gitterträger und die "
              "Screen-Oberkante absenken und festdrücken.")
add_step("main", f"Moving Heads unter die Traverse stecken ({len(HEADS)}×)", refs=[ref("moving_head.ldr", o) for _, _, o in HEADS],
         note="Von unten an die Seitentraversen über der Lower Stage und an die vordere Traverse drücken, "
              "Traverse dabei von oben gegenhalten.")
add_step("main", "Line-Arrays unter die Seitentraversen stecken (4×)", refs=[ref("line_array.ldr", o) for _, _, o in ARRAYS],
         note="Links und rechts neben dem Berg von unten an die Seitentraversen drücken, der Knick zeigt zum "
              "Publikum. Traverse dabei von oben gegenhalten.")

# ---------------- Weltzuordnung ----------------
MODELS = ["main", "traverse", "moving_head", "line_array"]
ASSY = {"traverse.ldr": TRUSS, "moving_head.ldr": [i for _, v, _ in HEADS for i in v],
        "line_array.ldr": [i for _, v, _ in ARRAYS for i in v]}


def step_parts(st):
    """alle physischen Teile eines Schritts (bei Baugruppen: alle Instanzen)"""
    out = list(st["ids"])
    for r in st["refs"]:
        f = r.split()[-1]
        if f == "traverse.ldr": out += TRUSS
        else:
            inst = HEADS if f == "moving_head.ldr" else ARRAYS
            o = tuple(float(v) for v in r.split()[2:5])
            out += next(v for _, v, oo in inst if tuple(map(float, oo)) == o)
    return out


def loose(placed, roots):
    placed = {i for i in placed if parts[i].cells}          # Figurenteile ohne Zellen stecken an den Beinen
    if not placed: return set()
    start = (roots & placed) if roots else None
    if not start:                                          # Baugruppe: groesste Komponente
        comps, rest = [], set(placed)
        while rest:
            s0 = rest.pop(); comp = {s0}; stack = [s0]
            while stack:
                x = stack.pop()
                for y in ADJ[x]:
                    if y in rest: rest.discard(y); comp.add(y); stack.append(y)
            comps.append(comp)
        return set(placed) - max(comps, key=len)
    seen = set(start); stack = list(start)
    while stack:
        x = stack.pop()
        for y in ADJ[x]:
            if y in placed and y not in seen: seen.add(y); stack.append(y)
    return set(placed) - seen


# Lose Teile (haengende Deckplatten, Gitter-Fliesen) in den Schritt ihres Halters verschieben
moved = 0
for m in MODELS:
    ms = [st for st in steps if st["model"] == m]
    roots = ROOTS if m == "main" else set()
    placed = set()
    for n, st in enumerate(ms):
        placed |= set(step_parts(st))
        bad = loose(placed, roots) & set(st["ids"])
        if bad and n + 1 < len(ms):
            st["ids"] = [i for i in st["ids"] if i not in bad]
            ms[n + 1]["ids"] = sorted(bad) + ms[n + 1]["ids"]
            placed -= bad; moved += len(bad)

# ---------------- Pruefungen ----------------
report = []
def rep(line=""): report.append(line)
ok_all = True

# 1) Vollstaendigkeit
cnt = Counter(i for st in steps if st["model"] == "main" for i in step_parts(st))
missing = [i for i in range(N) if cnt[i] == 0]
dup = [i for i, c in cnt.items() if c > 1]
sub_ids = {m: [i for st in steps if st["model"] == m for i in st["ids"]] for m in MODELS[1:]}
sub_ok = (sorted(sub_ids["traverse"]) == sorted(TRUSS) and sorted(sub_ids["moving_head"]) == sorted(HEADS[0][1])
          and sorted(sub_ids["line_array"]) == sorted(ARRAYS[0][1]))
rep(f"1. Vollständigkeit: {N} Teile, {len(missing)} fehlen, {len(dup)} doppelt, Baugruppen vollständig: "
    f"{'ja' if sub_ok else 'NEIN'}")
ok_all &= not missing and not dup and sub_ok

# 2) + 3)
conn_err, ins_err = [], []
for m in MODELS:
    ms = [(n, st) for n, st in enumerate(steps) if st["model"] == m]
    roots = ROOTS if m == "main" else set()
    placed = set()
    for n, st in ms:
        new = sorted(st["ids"], key=lambda i: -parts[i].ybot)
        for i in new:
            p = parts[i]
            if i in SNOT:                                      # von der Seite auf die Seitennoppen
                h = parts[SNOT[i]]
                d = (min(c[0] for c in p.cells) - min(c[0] for c in h.cells),
                     min(c[1] for c in p.cells) - min(c[1] for c in h.cells))
                front = {(c[0] + d[0] * s, c[1] + d[1] * s) for c in p.cells for s in (1, 2)}
                if any(parts[q].cells & front and parts[q].ytop < p.ybot and parts[q].ybot > p.ytop for q in placed):
                    ins_err.append((n, i, "von der Seite blockiert"))
            elif any(parts[q].ybot <= p.ytop and parts[q].cells & p.cells for q in placed):
                ins_err.append((n, i, "von oben blockiert"))
            placed.add(i)
        for r in st["refs"]:                                   # Baugruppen einsetzen
            f = r.split()[-1]
            o = tuple(float(v) for v in r.split()[2:5])
            grp = TRUSS if f == "traverse.ldr" else next(
                v for _, v, oo in (HEADS if f == "moving_head.ldr" else ARRAYS) if tuple(map(float, oo)) == o)
            cells = {c for i in grp for c in parts[i].cells}
            if f == "traverse.ldr":                            # von oben absenken
                lowest = max(parts[i].ybot for i in grp)
                hit = [q for q in placed if parts[q].cells & cells and parts[q].ytop < lowest]
                if hit: ins_err.append((n, hit[0], "Traverse lässt sich nicht absenken"))
            else:                                              # von unten: 3 Steine Freiraum unter der Baugruppe
                bottom = max(parts[i].ybot for i in grp)
                hit = [q for q in placed if parts[q].cells & cells and bottom <= parts[q].ytop < bottom + 3 * BH]
                if hit: ins_err.append((n, hit[0], f"{f} von unten blockiert"))
            placed |= set(grp)
        bad = loose(placed, roots)
        if bad: conn_err.append((n, len(bad), [parts[i].name for i in list(bad)[:5]]))
rep(f"2. Verbindung nach jedem Schritt: {len(conn_err)} Schritte mit losen Teilen "
    f"({moved} haltende Teile in den Schritt ihres Halters verschoben)")
for n, k, ex in conn_err[:20]: rep(f"   ! Schritt '{steps[n]['title']}': {k} lose Teile, z. B. {ex}")
rep(f"3. Einsetzbarkeit (von oben / Gitter von der Seite / Baugruppen von unten): {len(ins_err)} Probleme")
for n, i, why in ins_err[:20]:
    p = parts[i]; rep(f"   ! '{steps[n]['title']}': {p.name} bei {p.x},{p.y},{p.z}: {why}")
ok_all &= not conn_err and not ins_err

# 4) Traverse ruht auf Tuermen und Screen
t_low = [i for i in tv[yl[0]]]
held = [i for i in t_low if any(j in set(TOWER) | set(SUB["07_screen"]) for j in ADJ[i])]
rep(f"4. Endmontage: {len(held)} untere Traversen-Platten stecken auf Türmen/Screen")
ok_all &= len(held) > 0

sizes = [len(st["ids"]) for st in steps if st["ids"]]
per = Counter(st["model"] for st in steps)
rep(f"Schritte: Hauptmodell {per['main']}, Traverse {per['traverse']}, Moving Head {per['moving_head']}, "
    f"Line-Array {per['line_array']}; Teile je Schritt max {max(sizes)}, Mittel {sum(sizes) / len(sizes):.0f}")
rep("ERGEBNIS: " + ("ALLE PRÜFUNGEN BESTANDEN" if ok_all else "FEHLER GEFUNDEN"))
print("\n".join(report))

# ---------------- MPD fuer Stud.io ----------------
FILES = {"main": "yeezus_stage_anleitung.ldr", "traverse": "traverse.ldr", "moving_head": "moving_head.ldr",
         "line_array": "line_array.ldr"}
HEAD = {"main": "Yeezus Stage - Mount Yeezus (Bauanleitung)", "traverse": "Traverse (Baugruppe)",
        "moving_head": f"Moving Head (Baugruppe, {len(HEADS)}x)", "line_array": "Line-Array (Baugruppe, 4x)"}
ORIGIN = {"moving_head": HEADS[0][2], "line_array": ARRAYS[0][2]}
TURN = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]     # Publikum (-x) zeigt in Stud.io nach vorne (-z)


def turn(l):
    """Zeile um die Hochachse drehen: (x, y, z) -> (-z, y, x)"""
    f = l.split()
    p = [float(v) for v in f[2:5]]; M = [[float(v) for v in f[5 + 3 * r:8 + 3 * r]] for r in range(3)]
    p = [sum(TURN[r][k] * p[k] for k in range(3)) for r in range(3)]
    M = [[sum(TURN[r][k] * M[k][c] for k in range(3)) for c in range(3)] for r in range(3)]
    return " ".join(f[:2] + [fmt(v) for v in p] + [fmt(v) for row in M for v in row] + f[14:])


mpd = []
for m in MODELS:
    mpd += [f"0 FILE {FILES[m]}", f"0 {HEAD[m]}", f"0 Name: {FILES[m]}", "0 Author: Claude Code (generiert)",
            "0 !LDRAW_ORG Unofficial_Model", ""]
    for st in (s for s in steps if s["model"] == m):
        ids = sorted(st["ids"], key=lambda i: -parts[i].ybot)
        mpd.append(f"0 // {st['title']}")
        body = local_lines(ids, ORIGIN[m]) if m in ORIGIN else [l for i in ids for l in parts[i].lines()]
        if m in ("main", "traverse"): body = [turn(l) for l in body]     # Traverse intern mitgedreht
        mpd += body + [r if r.endswith("traverse.ldr") else turn(r) for r in st["refs"]] + ["0 STEP"]
    mpd += ["0 NOFILE", ""]
with open(os.path.join(OUT, "yeezus_stage_anleitung.mpd"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(mpd))

# ---------------- Schrittliste ----------------
NAMES = {"main": "HAUPTMODELL", "traverse": "BAUGRUPPE TRAVERSE (auf dem Tisch bauen)",
         "moving_head": f"BAUGRUPPE MOVING HEAD ({len(HEADS)}×)", "line_array": "BAUGRUPPE LINE-ARRAY (4×)"}
txt = ["Yeezus Stage – Schrittliste für den Stud.io Instruction Maker",
       "Stud.io nummeriert die Schritte je Modell; die Nummern hier entsprechen dieser Zählung.",
       "Hinweise (→) als Textfeld in den jeweiligen Schritt übernehmen.", ""]
for m in MODELS:
    txt.append(NAMES[m])
    for n, st in enumerate((s for s in steps if s["model"] == m), 1):
        k = len(st["ids"]) + len(st["refs"])
        txt.append(f"  {n:3d}. {st['title']}  ({k} {('Baugruppe' if k == 1 else 'Baugruppen') if st['refs'] else 'Teile'})")
        if st["note"]: txt.append(f"       → {st['note']}")
    txt.append("")
with open(os.path.join(HERE, "schritte.txt"), "w", encoding="utf-8") as f: f.write("\n".join(txt))
with open(os.path.join(HERE, "pruefbericht.txt"), "w", encoding="utf-8") as f: f.write("\n".join(report) + "\n")
sys.exit(0 if ok_all else 1)
