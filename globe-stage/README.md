# Globe Stage – Konzertbühne mit Erdkugel-Kuppel (LEGO MOC)

Stadion-Konzertbühne im Minifig-Maßstab: eine große, glatt gerundete Erdkugel-Kuppel,
LED-Ring mit Nebel und ein schmaler Truss-Ring mit Scheinwerfern. Wie im Stadion hängt der
Truss an Seilen (LEGO-Schnur 63142) unter einem dünnen Dach, das nur auf vier schlanken
Ecktürmen am Rand der Baseplate steht – die Sicht auf die Kuppel bleibt frei. Auf dem Dach liegt
das Album-Cover als Mosaik aus 3.600 Fliesen 1 × 1. Vorlage ist die Konzeptskizze in
[`reference/konzept-skizze.png`](reference/konzept-skizze.png), abgeglichen mit
Konzertfotos der echten Bühne.

**Bauanleitung:** [`Bauanleitung_Globe_Stage.pdf`](Bauanleitung_Globe_Stage.pdf) – 249 geprüfte Schritte
mit Teile-Kästen, Mosaik-Plan und Stückliste (siehe [Bauanleitung](#bauanleitung)).

![Hero](renders/globe_stage_hero.png)

| Dach-Mosaik (von oben) | Dach schräg |
|---|---|
| ![Mosaik](renders/globe_stage_dach_mosaik.png) | ![Dach](renders/globe_stage_dach.png) |

| Seite | Ohne Dach | Draufsicht ohne Dach |
|---|---|---|
| ![Seite](renders/globe_stage_seite.png) | ![Ohne Dach](renders/ohne_dach_schraeg.png) | ![Oben](renders/ohne_dach_oben.png) |

| Kuppel (ohne Aufbau) | Rückseite | Weltkarte von oben (vorne = unten) |
|---|---|---|
| ![Kuppel](renders/kuppel_front.png) | ![Hinten](renders/kuppel_hinten.png) | ![Karte](renders/kuppel_karte_oben.png) |

| Kuppel-Rundung (Nahaufnahme) | Truss an den Seilen | Dach von unten |
|---|---|---|
| ![Nah](renders/kuppel_nah.png) | ![Truss](renders/globe_stage_truss_detail.png) | ![Decke](renders/globe_stage_dach_unten.png) |

## Dateien

| Datei | Inhalt |
|---|---|
| `globe_stage.mpd` | Das Modell (LDraw Multi-Part, 15 Bauabschnitte als Submodelle + Seil-Untermodell) – in Stud.io, LeoCAD, LDView, BrickLink Studio öffnen |
| `globe_stage_bom.csv` | Stückliste (LDraw-ID, BrickLink-ID, Name, Farbe, Menge) |
| `globe_stage_bricklink.xml` | BrickLink Wanted List – direkt unter *Wanted → Upload* importierbar |
| `preview_nocage.mpd` | Vorschau ohne Ecktürme, Dach, Truss und Scheinwerfer (zum Anschauen der Kuppel) |
| `bully_mosaik_60x60.txt` | Raster des Dach-Mosaiks, 60 Zeilen × 60 Zeichen (K = Schwarz, D = Dark Bluish Gray, L = Light Bluish Gray, W = Weiß), Zeile 1 = hinten, von vorne gelesen |
| `bully_mosaik_60x60_pearl.txt` | Alternative mit 5 Farben (+ P = Pearl Dark Gray), feinere Hauttöne – `MOSAIC_FILE=… python3 generate_globe_stage.py` |
| `Bauanleitung_Globe_Stage.pdf` | Bauanleitung (A4 quer): Vorbereitung, Prüfbericht, 249 Schritte, Mosaik-Plan, Stückliste |
| `anleitung/` | Skripte für die Anleitung: `plan_steps.py` (Schritte planen + prüfen), `make_pdf.py` (PDF bauen) |
| `generate_globe_stage.py` | Generator, der alle drei Dateien erzeugt |
| `renders/` | Renderings der aktuellen Version |

## Kennzahlen

- **10.876 Teile**, 179 Positionen (Teil × Farbe), keine Minifiguren – davon 3.600 Fliesen im Dach-Mosaik
- **Echte Beleuchtung vorbereitet**: LED-Kanal im LED-Ring (Streifen ca. 1,2 m) und 24 Scheinwerfer mit LED, gemeinsame USB-Versorgung
- **Grundfläche** 64 × 64 Noppen (4 Baseplates 32 × 32, ca. 51 × 51 cm)
- **Höhe** ca. 41 cm (bis Oberkante Dach)
- **Kuppel** Ø 48 Noppen, 14 Lagen, Erd-Mosaik (orthografische Projektion auf Nordafrika/Europa, Afrika zeigt zur Front)
- **Truss-Ring** Ø 59 Noppen, ca. 3,5 Noppen breit, hängt an 8 Seilen 63142
- **Dach** 64 × 64 Noppen, nur 2 Plattenlagen + Attika, auf 4 Ecktürmen (je 2 Gitterträger 95347 diagonal pro Ebene)
- **Dach-Mosaik** 60 × 60 Fliesen innerhalb der Attika (48 × 48 cm)

## Aufbau (Submodelle = Bauabschnitte)

1. **Arena-Boden** – 4 × Baseplate 32 × 32 schwarz
2. **Basis** Ø 64, 2 Lagen schwarz, Rand mit Fliesen
3. **Laufsteg** Ø 56, dunkelgrau, Fliesen-Oberfläche
4. **LED-Ring** Ø 52 – trans-klare Leuchtreihe mit LED-Kanal dahinter, darüber weiße Brückenlage (siehe „LED-Beleuchtung“)
5. **Kuppel unten** (Lagen 0–7) mit **Deck 1**: hohle Kuppel, auf Höhe von Lage 7 mit drei kreuzweisen Plattenlagen überspannt
6. **Kuppel Mitte** (Lagen 8–11) mit **Deck 2**
7. **Kuppel oben** (Lagen 12–13, massiv)
8. **Innenstützen** – 2 × 2-Säulen im Hohlraum unter den Decks
9. **Kuppel-Rundung**: ausschließlich 1 × 1-Teile (Cheese-Slopes, Platten, Fliesen) auf jeder Stufe, dazu eine kleine Kappe auf dem Plateau (siehe unten)
10. **Nebel** – 2 × 2-Kuppelsteine + „Swirl“-Platten auf dem LED-Ring
12. **Ecktürme** – 4 Türme an den Ecken der Baseplate, je 4 Ebenen aus 2 Gitterträgern 95347 (2 × 2 × 10) auf der Diagonale, dazwischen Platten 4 × 4
13. **Truss-Ring** Ø 59 – schmaler Plattenring (untere Lage radial, obere Lage als Verbund gelegt, sodass der Boden schon ohne Wände ein Stück ist), zwei Wände aus normalen schwarzen Steinen (2 Lagen), Obergurt aus 2 Plattenlagen, liegt in den Seilschlingen
14. **Scheinwerfer** – 24 hängende Lampen unter dem Truss, jeweils mit LED (siehe „LED-Beleuchtung“)
15. **Seile** – 8 Schnüre 63142 (String with End Studs 30L) als Schlingen zwischen Decke und Truss
16. **Dach** 64 × 64 – Decke und Dachplatten (um 8 Noppen versetzt verlegt), umlaufende Attika 1 Stein hoch, Kabel-Clips unter der Decke
17. **Dach-Mosaik** – Album-Cover aus 3.600 Fliesen 1 × 1 (3070b) in 4 Grautönen (siehe unten)

## Kuppel-Rundung

Die Rundung ist bewusst nur aus 1 × 1-Teilen aufgebaut, ohne längliche Slopes.

Für jede Kuppellage und jede radiale Reihe misst der Generator, wie breit die freie Stufe
der Lage darunter ist. Dann füllt er jede Stufenzelle passend zur idealen Kuppellinie
(steigt über die Stufenbreite um eine Steinhöhe) auf:

| Sollhöhe der Zelle | Aufbau |
|---|---|
| hoch (direkt an der nächsten Lage) | 1 × 1-Platte + 1 × 1-Cheese-Slope (füllt die volle Steinhöhe) |
| mittel | 1 × 1-Cheese-Slope |
| niedrig (breite Terrassen außen) | 1 × 1-Fliese |

Auf dem Plateau sitzt eine kleine Kappe (1 Plattenlage, Rand mit Cheese-Slopes). Alle übrigen
offenen Noppen der Kuppel sind mit Fliesen in Erdfarbe abgedeckt. So entsteht eine
gleichmäßige „Schuppen“-Rundung wie bei einer glatten Kuppel.

Verbaut sind 1.468 Cheese-Slopes 1 × 1 (54200), 427 Platten 1 × 1 als Unterbau und die
Fliesen der Oberfläche.

## Dach-Mosaik (Album-Cover)

Das Cover ist als Graustufen-Mosaik 60 × 60 aus Fliesen 1 × 1 umgesetzt – genau die Fläche
innerhalb der Attika. Das Raster erzeugt [`tools/mosaic/make_mosaic.py`](../tools/mosaic/make_mosaic.py),
das mehrere Varianten baut und jede gegen die Vorlage bewertet:

- **fern (ΔL\*)** – Helligkeitsabweichung nach leichter Unschärfe, so wie ein Mosaik aus
  Betrachtungsabstand wirkt (kleiner = besser)
- **detail (SSIM)** – strukturelle Ähnlichkeit im Raster selbst (größer = besser)

| Runde | Ansatz | Ergebnis |
|---|---|---|
| 1 | nächste Farbe / Fehlerdiffusion, 4–6 Grautöne | Tonwerte ok, aber der Grill ist nur ein graues Feld, Diffusion erzeugt Pixelrauschen |
| 2 | Lichter anheben (Metall-Glanz) + Lokalkontrast | Grill leuchtet, Mund und Nase klar, Falten sichtbar |
| 3 | nur Standardfarben, leichte Diffusion, einzelne Ausreißer-Fliesen bereinigt | **gewählt** – klare Flächen, kaum „Krümel“, Grill als Blickfang |

Verwendet werden nur gut erhältliche Farben: Schwarz 1.482, Dark Bluish Gray 1.491,
Light Bluish Gray 486, Weiß 141. Die 5-Farben-Variante mit Pearl Dark Gray misst etwas besser
(SSIM 0,76 statt 0,68) und liegt als `bully_mosaik_60x60_pearl.txt` bei; Pearl Dark Gray ist
als 1 × 1-Fliese aber deutlich seltener und teurer.

Das Mosaik ist so orientiert, dass es von vorne (Publikumsseite) richtig herum lesbar ist.
Der Generator prüft, dass alle 3.600 Felder belegt sind; das Rendering wurde per Korrelation
gegen das Raster gegengeprüft (r = 0,99).

## Dach, Ecktürme und Seil-Aufhängung

Wie bei der echten Bühne hängt der Truss-Ring von oben. Unter dem Ring steht nichts, nur die
vier Ecktürme ganz außen an der Baseplate:

| Bauteil | Aufbau |
|---|---|
| **Seile** | 8 × LEGO-Schnur 63142 (String with End Studs 30L, 24 cm; BrickLink `x127c30pb01`) als Schlinge: beide Endnoppen stecken unten in der Decke, das Seil läuft außen am Truss herunter, unter dem Truss durch und innen wieder hoch. Der Ring liegt in den Schlaufen – wie ein „Basket Hitch“ beim echten Rigging |
| **Hängehöhe** | ergibt sich aus der Seillänge: 576 LDU Schnur zwischen den Endnoppen, 80 LDU (4 Noppen) unter dem Truss, bleiben 248 LDU (ca. 10 cm) je Seite – der Generator setzt den Truss genau auf diese Höhe |
| **Ecktürme** | an jeder Ecke 4 Ebenen aus je 2 Gitterträgern 95347 auf der Diagonale (außen und innen), dazwischen Platten 4 × 4. Von der Bühne aus stehen die beiden Träger hintereinander und wirken wie einer |
| **Decke** | Plattenlage 64 × 64 (Platten 16 × 16 und 8 × 16, schwarz) |
| **Dachplatten** | zweite Plattenlage, um 8 Noppen versetzt verlegt, damit jede Fuge der Decke überbrückt ist |
| **Attika** | umlaufender Randträger, 2 Noppen breit, 1 Stein hoch – macht die Dachkanten zwischen den Türmen steif und rahmt das Mosaik |

**Aufbau-Reihenfolge:** Basis, Kuppel und Ecktürme bauen. Die 8 Seile unten in die Decke stecken
(Positionen siehe Modell) und das Dach auf die Türme setzen. Dann den fertigen Truss-Ring mit
Scheinwerfern von unten in die Schlaufen einhängen: je ein Seil unter dem Ring durchziehen.

### Statik-Iterationen

Der Generator rechnet bei jedem Lauf eine grobe, konservative Statik-Abschätzung mit
(Noppen-Klemmkraft 1,5 N je Noppe, Fugen halbieren die Biegesteifigkeit). Verglichen wurden
drei Turm-Varianten – alle mit dünnem Dach, Seilen und Dach-Mosaik (Dach inkl. Mosaik ca. 1,4 kg):

| | schlank 2 × 2 (1 Träger) | **diagonal (2 Träger), gewählt** | 4 × 4 (4 Träger, bisher) |
|---|---|---|---|
| Gitterträger gesamt | 16 | **32** | 64 |
| Kraft je Seil-Endnoppe | 0,32 N (21 %) | **0,32 N (21 %)** | 0,32 N (21 %) |
| Kippmoment je Trägerfuge | 48 Nmm | **192 Nmm** | 384 Nmm |
| seitliche Kraft am Dach bis zum Nachgeben | 1,0 N (≈ 100 g) | **3,9 N (≈ 400 g)** | 7,8 N (≈ 800 g) |
| Schiefstellung bis Instabilität | 20 mm | **77 mm** | 150 mm |
| Durchbiegung Dachrand | 1,22 mm | **1,10 mm** | 1,10 mm |
| Bewertung | kritisch – kippt bei leichtem Anstoßen | **OK** | OK |

Das dünne Dach (2 Plattenlagen + Attika statt Trägerrost) biegt sich auch mit den 3.600
Mosaik-Fliesen (ca. 400 g) nur etwa 1 mm durch. Die Seile sind unkritisch: jede Endnoppe trägt ca. 0,3 N.
Der hängende Ring kann wie beim Original leicht pendeln, trifft dabei aber weder Kuppel noch Türme.

| Dach von unten | Eckturm (Detail) | Eckturm hinten links mit Kabelweg unter der Decke |
|---|---|---|
| ![Decke](renders/globe_stage_dach_unten.png) | ![Turm](renders/globe_stage_turm.png) | ![Kabelecke](renders/globe_stage_kabelecke.png) |

## LED-Beleuchtung

Beide Lichtquellen sind für echte LEDs vorbereitet und hängen an **einer** USB-Versorgung (5 V).
Beide Kabel kommen hinten aus dem Modell: das des LED-Streifens aus dem Kabeltunnel hinten Mitte,
das der Scheinwerfer am Eckturm hinten links (von vorne gesehen).

### LED-Ring

Der LED-Ring ist für einen echten LED-Streifen vorbereitet:

| | |
|---|---|
| **Kanal** | ringsum direkt hinter der trans-klaren Reihe, 1 Noppe tief (8 mm), 1 Stein hoch (9,6 mm, über den Noppen ca. 7,9 mm frei) |
| **Länge** | ca. 1,2 m (Kanalmitte bei Ø ≈ 47 Noppen) |
| **Streifen** | 5-mm-COB-LED-Streifen, 5 V / USB, kalt- oder neutralweiß (COB = durchgehende Lichtlinie ohne Punkte, wie der Ring auf den Konzertfotos). Alternativ die Strip-Lights eines LEGO-Beleuchtungssets |
| **Montage** | Klebeseite an die weiße Innenwand des Kanals, Licht nach außen. Die trans-klaren Steine davor wirken als Diffusor |
| **Kabel** | hinten Mitte ein senkrechter Schacht vom Kanal bis zur Baseplate, von dort ein Tunnel in der untersten Basis-Lage nach außen (1 Noppe breit, 1 Stein hoch – für das Kabel, der Stecker bleibt außen) |

**Statik:** Die Lage über dem Kanal besteht aus radialen 1 × 4-Steinen. Jeder liegt außen
auf der trans-klaren Reihe und innen auf der Wand und überbrückt so den Kanal. Die Kuppel steht
unverändert darauf. Den Tunnel überbrücken quer liegende 1 × 3-Steine. Der Statik-Check prüft
beides mit.

**Einbau:** Streifen einlegen und Kabel durch Schacht und Tunnel führen, **bevor** die
obere LED-Ring-Lage (radiale 1 × 4-Steine) aufgesetzt wird. Der Streifen ist kein LEGO-Teil
und steht deshalb nicht in Stückliste und BrickLink-Liste.

| Kanal im Schnitt (obere Lage ausgeblendet) | Kanal nah | LED-Ring von außen | Kabeltunnel hinten |
|---|---|---|---|
| ![Schnitt](renders/led_kanal_schnitt.png) | ![Nah](renders/led_kanal_schnitt_nah.png) | ![Ring](renders/kuppel_led_ring.png) | ![Tunnel](renders/kuppel_kabeltunnel.png) |

### Scheinwerfer am Truss

| | |
|---|---|
| **Lampe** | Gehäuse = schwarzer 1 × 1-Rundstein (hohl), darin eine kleine LED (z. B. „Dot Light“ aus einem LEGO-Beleuchtungsset, 5 V), Linse = trans-klare 1 × 1-Rundplatte darunter |
| **Draht an der Lampe** | direkt neben jeder Lampe ist ein 1 × 1-Loch durch beide Truss-Plattenlagen. Der Draht geht seitlich aus der Lampe (zwischen Gehäuse und Linse) und durch das Loch nach oben |
| **Truss-Kanal** | zwischen innerer und äußerer Truss-Wand verläuft ringsum ein ca. 1 Noppe breiter Hohlraum. Dort werden die 24 Drähte gesammelt (z. B. mit Verteiler-Platinen des Lichtsets) |
| **Sammelleitung** | durch ein Loch im Obergurt (in der Seilreihe hinten links) auf den Truss und am äußeren Seil entlang nach oben |
| **Unter der Decke** | an der schwarzen Deckenunterseite entlang (schwarz auf schwarz, von vorne unsichtbar), gehalten von 4 Platten 1 × 1 mit Clip (4081b), bis direkt vor den inneren Träger des Eckturms hinten links – das Dach selbst bleibt frei für das Mosaik |
| **Anschluss** | am Eckturm entlang nach unten (im Gitter geführt oder mit kleinen Clips) und an der Ecke der Baseplate nach außen, wie die Kabel an echten Bühnentürmen |

**Statik:** Die Löcher sind einzelne Zellen in kreuzweise verbauten Plattenlagen; Truss und
Dach bleiben durchgehend verbunden. Der Generator prüft neben der Statik auch den Kabelweg:
Lampenlöcher frei, Obergurt-Loch über dem Kanal, Weg unter der Decke frei (nur die Clips),
endet direkt am Eckturm, Mosaik vollständig, LED-Kanal und Schacht leer.

**Einbau:** LEDs und Drähte einsetzen, bevor die Truss-Wände und der Obergurt aufgesetzt
werden. Nach dem Einhängen des Rings die Sammelleitung am Seil hoch und in die Clips unter der
Decke legen, dann am Eckturm hinunter.

| Truss-Kanal im Schnitt (Wände/Obergurt ausgeblendet) | Scheinwerfer von unten |
|---|---|
| ![Kanal](renders/truss_kanal_schnitt.png) | ![Unten](renders/globe_stage_scheinwerfer_unten.png) |

## Statik & Prüfung

Der Generator prüft das Modell nach jedem Lauf automatisch:

- **0 nicht verbundene Teile**: Jedes Teil hängt über Noppenverbindungen an der Baseplate.
- **0 schwebende Teile**: Jedes Teil sitzt auf mindestens einer Noppe. Die 214 Ausnahmen hängen mit Klemmkraft von oben: die Deckenplatten (an den Dachplatten), die Seil-Endnoppen und Kabel-Clips (in der Decke), Teile der unteren Truss-Plattenlage (kreuzweise unter der zweiten Lage verbaut) und die Scheinwerfer. Der Truss als Ganzes liegt in den Seilschlingen – der Check wertet das als Verbindung.
- **Statik-Abschätzung**: Seilkräfte, Kippsicherheit der Ecktürme und Durchbiegung des Dachs (siehe „Statik-Iterationen“). Die Turm-Variante lässt sich mit `TOWER_STYLE=slim|diag|full` umschalten.
- **0 Kollisionen**: kein Volumen doppelt belegt
- Alle Steine liegen exakt im Noppenraster.

Die Renderings entstehen mit dem Headless-Renderer in [`../tools/ldraw-render`](../tools/ldraw-render)
(three.js LDrawLoader + Chromium, echte LDraw-Teilegeometrie).

## Bauanleitung

[`Bauanleitung_Globe_Stage.pdf`](Bauanleitung_Globe_Stage.pdf) ist aus dem Modell generiert und in fünf
Abschnitte gegliedert:

| | Abschnitt | Inhalt |
|---|---|---|
| A | Basis und Kuppel | Lage für Lage von unten, große Lagen in Vierteln/Achteln, Innenstützen, LED-Kanal mit Kabel und Streifen |
| B | Ecktürme | 4 Ebenen Gitterträger |
| C | Truss-Ring | Baugruppe auf dem Tisch: Boden in Achteln, Wände, Scheinwerfer mit LEDs von unten, Drähte, Obergurt |
| D | Dach mit Mosaik | Baugruppe: Decke + versetzte Dachplatten, Attika, Mosaik in 6 Streifen mit Legeplan |
| E | Endmontage | Hilfsstützen, Ring einsetzen, Dach aufsetzen, Clips, Seile, Kabel |

Jeder Schritt zeigt die neuen Teile farbig und die bereits verbauten blass, dazu einen Kasten mit allen
Teilen des Schritts. Arbeitsschritte ohne Steine (LEDs, Kabel, Montage) sind gelb markiert.

**Prüfung der Bauschritte** ([`anleitung/plan_steps.py`](anleitung/plan_steps.py)) – vor dem Erstellen
wird jeder Schritt gegen das Modell geprüft:

- **Vollständigkeit** – jedes Teil genau einmal
- **Verbindung** – nach jedem Schritt hängt alles zusammen (Hauptmodell an den Grundplatten,
  Baugruppen in sich), es gibt keinen Zwischenstand mit losen Teilen
- **Einsetzbarkeit** – jedes Teil lässt sich von oben aufstecken (darüber ist noch nichts), nur Teile an
  Unterseiten (Scheinwerfer, Clips, Seile) werden von unten eingesteckt
- **Endmontage** – Ring passt zwischen den Türmen durch und hängt frei über der Kuppel, Dach lässt
  sich aufsetzen, Seil-Enden sind erreichbar, Hilfsstützen stehen eben

Dabei gefunden und behoben: Die zwei Bodenplatten-Lagen des Truss-Rings lagen teilweise parallel und
hielten ohne die Wände nicht zusammen – beim Bauen wäre der Ring in 15 Stücke zerfallen. Die obere Lage
wird jetzt mit einer Verbund-Packung gelegt (`bond_layer`), die alle Platten der unteren Lage zu einem
Stück verbindet; der Generator prüft das.

## Neu erzeugen

```bash
pip install numpy global-land-mask     # Landmaske für das Erd-Mosaik
python3 globe-stage/generate_globe_stage.py

# Bauanleitung (braucht den Renderer aus tools/ldraw-render und reportlab)
python3 globe-stage/anleitung/plan_steps.py build            # Schritte planen + prüfen
node tools/ldraw-render/steps.js anleitung.mpd build/steps_jobs.json build/shots
node tools/ldraw-render/steps.js thumbs.mpd build/thumbs_jobs.json build/thumbs
node tools/ldraw-render/steps.js anleitung.mpd build/extra_jobs.json build/shots
python3 globe-stage/anleitung/make_pdf.py build globe-stage/Bauanleitung_Globe_Stage.pdf
```

Alle Parameter (Kuppelprofil, Kartenmitte, Wolken, Seil- und Lampenpositionen, Turm-Variante, Farben) stehen im Skript.

## Hinweise & Grenzen

- **Schräge Spotlight-Strahlen** aus der Skizze lassen sich nicht aus Steinen bauen. Stattdessen hängen 24 Scheinwerfer mit echten LEDs unter dem Truss.
- **Weltkarte:** Die Kuppel war bis v14 seitenverkehrt (Arabien lag von vorne gesehen links). Beim Prüfen der Draufsichten für das Mosaik aufgefallen und korrigiert – jetzt liegt Westafrika links, Arabien rechts.
- **Seile im Modell:** LDraw hat keine fertige Datei für 63142. Das Seil ist im MPD als eigenes Untermodell `seil_63142.ldr` aus Primitiven nachgebildet (Endnoppen + dünne Schnur) und steht in Stückliste und BrickLink-Liste als `x127c30pb01`. In Stud.io erscheint es als Untermodell, nicht als Katalogteil.
- **Kosten** grob geschätzt 650–950 € über BrickLink (Cheese-Slopes, 1 × 1-Platten und -Fliesen sind günstig). Die größten Posten sind:
  - 4 schwarze 32 × 32-Baseplates
  - 3.600 Fliesen 1 × 1 für das Dach-Mosaik (ca. 100–150 €)
  - 32 Gitterträger 95347
  - 22 Platten 16 × 16 und 23 Platten 8 × 16 für das Dach
  - die rund 1.470 Cheese-Slopes der Kuppel
  - die schwarzen Kernsteine der Kuppel
