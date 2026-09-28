#!/usr/bin/env python3
"""Pythagoras- und Beinahe-Tripel fuer schraege LEGO-Verbindungen.

Aufruf:  python3 winkel.py [max_kathete=24] [toleranz_studs=0.1] [--winkel GRAD]
Listet Kathetenpaare (a, b) in Studs, deren Diagonale c fast ganzzahlig ist. Exakte Tripel
(Fehler 0) verbinden Noppe auf Noppe; kleine Fehler gleichen Scharnierplatten/Drehteller aus.
Mit --winkel werden nur Loesungen nahe dem Wunschwinkel (+-3 Grad) gezeigt.
"""
import math, signal, sys

signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # sauber mit head/less

args = [a for a in sys.argv[1:] if not a.startswith("--")]
nmax = int(args[0]) if len(args) > 0 else 24
tol = float(args[1]) if len(args) > 1 else 0.1
want = None
if "--winkel" in sys.argv:
    want = float(sys.argv[sys.argv.index("--winkel") + 1])

rows = []
for a in range(1, nmax + 1):
    for b in range(a, nmax + 1):
        c = math.hypot(a, b)
        err = abs(c - round(c))
        if err <= tol:
            ang = math.degrees(math.atan2(a, b))
            if want is not None and min(abs(ang - want), abs(90 - ang - want)) > 3: continue
            rows.append((err, a, b, round(c), ang))
rows.sort(key=lambda r: (r[0] > 1e-9, r[3], r[0]))
print(f"{'a':>3} {'b':>3} {'c':>3}  {'Fehler':>7}  Winkel")
for err, a, b, c, ang in rows:
    tag = "exakt" if err < 1e-9 else f"{err:.3f}"
    print(f"{a:>3} {b:>3} {c:>3}  {tag:>7}  {ang:5.1f}° / {90 - ang:5.1f}°")
