# Geometrie, Maße und Verbindungsmathematik

## Grundmaße

| Größe | mm | LDU | Merksatz |
|---|---|---|---|
| Noppenraster (1 Stud) | 8,0 | 20 | Zellzentrum = (i + 0,5) · 20 |
| Platte / Tile | 3,2 | 8 | 3 Platten = 1 Stein |
| Stein (Brick) | 9,6 | 24 | |
| Noppe Ø / Höhe | 4,8 / 1,7 | 12 / 4 | passt in Technic-Loch und Anti-Stud |
| Stange (Bar) Ø | 3,18 | 8 | passt in Clip, Hohlnoppe, Minifig-Hand, 1x1-Rundplatten-Unterseite |
| Technic-Loch Ø | 4,8 | 12 | Pin/Achse; Noppe passt, erzeugt aber Spannung |

**Die wichtigste Verhältniszahl: 5 Platten = 2 Studs (40 LDU).** Daraus folgt die ganze SNOT-Mathematik:

| Studs (Breite) | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Platten (Höhe) | 2,5 | 5 | 7,5 | 10 | 12,5 | 15 |
| Umsetzung | 2 Pl. + ½ Pl.-Versatz | 1 Stein + 2 Pl. | 2 Steine + 1 Pl. + ½ | 3 Steine + 1 Pl. | 4 Steine + ½ | 5 Steine |

Halbe Platten (4 LDU) entstehen nur über Teile mit eingebautem Versatz (Headlight, Brackets) –
Ganzzahl-Kombinationen immer bevorzugen (gerade Stud-Zahlen seitlich bauen).

## LDraw-Konventionen

- Y zeigt nach **unten**; Baseplate-Oberfläche y = 0, höher bauen = y negativer.
- Zeile: `1 <farbe> x y z a b c d e f g h i <teil>.dat` (Welt = M · lokal).
- Yaw-Rotationen um Y: 0° `1 0 0 0 1 0 0 0 1`, 90° `0 0 -1 0 1 0 1 0 0`,
  180° `-1 0 0 0 1 0 0 0 -1`, 270° `0 0 1 0 1 0 -1 0 0`.
- Seitlich kippen (SNOT-Fliese, Front zeigt nach −x): `0 1 0 0 0 -1 -1 0 0` (so im Yeezus-Generator
  für Gitterfliesen auf 11211 genutzt) – neue Matrizen immer im Render prüfen.
- MPD: `0 FILE x.ldr` … `0 NOFILE`, Hauptmodell referenziert Submodelle mit Farbe 16.
- n-Stud-Teil über Zellen a..b → Zentrum (a+b)/2 · 20 + 10; 2x2-Teile zentrieren auf Rasterkreuzungen.

## Teile-Ursprünge (vor Einsatz mit `scripts/ldbbox.py` prüfen)

Die Bounding-Box verrät den Ursprung: y von −4 (Noppe) bis +Höhe → Ursprung **oben**;
y von −Höhe bis 0 → Ursprung **unten** (direkt auf die Auflagefläche setzen).

| Teil | y-Ausdehnung | Ursprung |
|---|---|---|
| Bricks 3005 … 3001, Plates 3024 …, Tiles 3070b … | −4…24 / −4…8 / 0…8 | oben |
| Slopes 3040b, 3039, 4286, 60477, 60481 (−4…48), 4460b (−4…72) | | oben, Schräge fällt nach −z ab |
| Umgedrehte Slopes 3665a, 3660a | −4…24 | oben |
| Cheese 54200, 85984 | −15,6…0 | **unten** |
| Curved 11477, 15068, 93273 | −16…0 | **unten** |
| Curved 61678 (4x1), 50950 (3x1) | 0…24 | oben (ohne Noppe) |
| Slope-Platte 92946 | −16…8 | Sonderfall – im Render prüfen |
| Rundplatte mit Wirbel 15470 | −18…0 | unten |
| Gitterträger 95347 | −4…240 | oben |
| Brackets 99781 (down) −4…20, 99780 (up) −12…8, 44728 −4…40, 99207 −32…8 | | Ursprung = Plattenebene |

Slope-Richtung im Generator: Gefälle nach −z ist Standard; Richtung d → Rotation
`{(+1,0): 90, (−1,0): 270, (0,+1): 180, (0,−1): 0}`.

## SNOT-Versätze

- **87087 / 11211 / 30414** (Stud an der Seite): Noppenbasis bündig mit der Wandfläche, Noppe ragt
  4 LDU heraus (Box z −14…10). Eine angesetzte Platte steht 8 LDU vor.
- **4070 Headlight**: Seitennoppe ist ½ Platte (4 LDU) zurückgesetzt – Noppenspitze bündig mit der
  Fläche (Box z −10…10). Angesetzte Platte steht nur 4 LDU vor → **½-Platten-Relief** gegenüber 87087.
  Die Rückseite hat eine Aussparung, die wie ein Anti-Stud greift.
- **Brackets** (99780/99781/44728/99207/2436b): Seitenfläche liegt je nach Typ ½ Platte versetzt;
  Headlight, Stud-Brick und Bracket nebeneinander ergeben aufeinanderfolgende ½-Platten-Stufen.
- **32952** (1x1x1⅔ mit Seitennoppen): 5 Platten hoch = 2 Studs → quadratischer SNOT-Würfel mit 2 Studs.
- **4733 / 47905**: Noppen auf 4 bzw. 2 gegenüberliegenden Seiten – Kern für Lowell-Kugel und Säulen.

## Halbe-Noppe-Versatz (Offset, „AZMEP")

- **Jumper 1x2** (3794b, neu 15573): eine Noppe mittig → ½ Stud in einer Achse.
- **Jumper 2x2** (87580): Noppe auf der Rasterkreuzung → ½ Stud in beiden Achsen; zentriert 1x1-Teile
  auf geraden Breiten.
- Einsatz: Symmetrie bei ungerader/gerader Breite, Verjüngen um 1 Stud (je ½ pro Seite),
  Mauerverband, Fugenversatz, Details genau auf der Mittelachse.
- Kombination Jumper + Headlight + 1x1-Platte ergibt ¼- und ¾-Platten-Versätze (Feinjustage).

## Winkel ohne Raster

**Pythagoras-Tripel** – beide Enden treffen genau auf Noppen:

| Katheten | Hypotenuse | Winkel | Bemerkung |
|---|---|---|---|
| 3, 4 | 5 | 36,9° / 53,1° | Standard; 1x6-Platte verbindet Noppen im Abstand 5 |
| 6, 8 | 10 | 36,9° | doppelt, stabiler |
| 5, 12 | 13 | 22,6° | flache Schräge |
| 8, 15 | 17 | 28,1° | |
| 7, 24 | 25 | 16,3° | sehr flach |
| 20, 21 | 29 | 43,6° | fast 45° |

**Beinahe-Tripel** (Scharnierplatten haben etwas Spiel): für ≈45° 12-12-17 (16,97), 17-17-24 (24,04),
5-5-7 (7,07), 7-7-10 (9,90); 8-9-12 (12,04) ergibt 41,6°. Berechnen mit `scripts/winkel.py`.

Verbindungsmittel:
- Platte diagonal nur an den End-Noppen aufsetzen (Mittelnoppen frei) – legal und üblich.
- **Scharnierplatten** 2429c01 (1x4 drehbar) für Wandecken; die kurze Seite ist 5 statt 6 Studs, weil
  sich die Dreiecksseiten an den Plattenecken treffen.
- **Drehteller** 3680 + 3679 (2x2) oder 1x1-Rundplatten (6141) als Drehpunkt: beliebiger Winkel.
- **Rastscharniere** 44301a/44302a: feste Stufen, tragen mehr Last als freie Clips.
- **Clip + Stange**: stufenlos, aber nur für leichte Teile.

## Clip/Stange (3,18-mm-System)

- Stangen: 87994 (3L), 30374 (4L), Griffe an Platten 60478 (Ende), 48336 (Seite), 26047 (1x1 rund).
- Clips: 4085c (1x1 vertikal, dick), 61252 / 6019 (1x1 horizontal), 63868 (1x2 am Ende), 15712 / 2555
  (Fliese 1x1 mit Clip), 4081b (1x1 Licht-Clip).
- Stange passt in Hohlnoppen (3062b, 4589, 6141-Unterseite) → Säulen, Äste, Kabel, Masten.
- Kugelgelenke 14417/14418/14419 für frei orientierbare Anbauten (Scheinwerfer, Arme).
