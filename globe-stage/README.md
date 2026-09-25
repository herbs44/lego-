# Globe Stage – Konzertbühne mit Erdkugel-Kuppel (LEGO MOC)

Stadion-Konzertbühne im Minifig-Maßstab: eine große, glatt gerundete Erdkugel-Kuppel,
LED-Ring mit Nebel und ein schmaler Truss-Ring mit Scheinwerfern. Wie im Stadion hängt der
Truss an Kettenzügen unter einem Dach, das nur auf vier Ecktürmen am Rand der Baseplate
steht – die Sicht auf die Kuppel bleibt frei. Vorlage ist die Konzeptskizze in
[`reference/konzept-skizze.png`](reference/konzept-skizze.png), abgeglichen mit
Konzertfotos der echten Bühne.

![Hero](renders/globe_stage_hero.png)

| Seite | Ohne Dach | Draufsicht ohne Dach |
|---|---|---|
| ![Seite](renders/globe_stage_seite.png) | ![Ohne Dach](renders/ohne_dach_schraeg.png) | ![Oben](renders/ohne_dach_oben.png) |

| Kuppel (ohne Aufbau) | Rückseite |
|---|---|
| ![Kuppel](renders/kuppel_front.png) | ![Hinten](renders/kuppel_hinten.png) |

| Kuppel-Rundung (Nahaufnahme) | Truss an den Kettenzügen | Dach von unten |
|---|---|---|
| ![Nah](renders/kuppel_nah.png) | ![Truss](renders/globe_stage_truss_detail.png) | ![Decke](renders/globe_stage_dach_unten.png) |

## Dateien

| Datei | Inhalt |
|---|---|
| `globe_stage.mpd` | Das Modell (LDraw Multi-Part, 15 Bauabschnitte als Submodelle) – in Stud.io, LeoCAD, LDView, BrickLink Studio öffnen |
| `globe_stage_bom.csv` | Stückliste (LDraw-ID, BrickLink-ID, Name, Farbe, Menge) |
| `globe_stage_bricklink.xml` | BrickLink Wanted List – direkt unter *Wanted → Upload* importierbar |
| `preview_nocage.mpd` | Vorschau ohne Ecktürme, Dach, Truss und Scheinwerfer (zum Anschauen der Kuppel) |
| `generate_globe_stage.py` | Generator, der alle drei Dateien erzeugt |
| `renders/` | Renderings der aktuellen Version |

## Kennzahlen

- **7.474 Teile**, 178 Positionen (Teil × Farbe), keine Minifiguren
- **Echte Beleuchtung vorbereitet**: LED-Kanal im LED-Ring (Streifen ca. 1,2 m) und 24 Scheinwerfer mit LED, gemeinsame USB-Versorgung
- **Grundfläche** 64 × 64 Noppen (4 Baseplates 32 × 32, ca. 51 × 51 cm)
- **Höhe** ca. 43 cm (bis Oberkante Dach)
- **Kuppel** Ø 48 Noppen, 14 Lagen, Erd-Mosaik (orthografische Projektion auf Nordafrika/Europa, Afrika zeigt zur Front)
- **Truss-Ring** Ø 59 Noppen, ca. 3,5 Noppen breit, hängt an 8 Kettenzügen
- **Dach** 64 × 64 Noppen auf 4 Ecktürmen (je 4 × 4 Noppen aus 16 Gitterträgern 95347)

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
12. **Ecktürme** – 4 Türme 4 × 4 an den Ecken der Baseplate, je 4 Ebenen aus 4 Gitterträgern 95347 (2 × 2 × 10), dazwischen Platten 4 × 4
13. **Truss-Ring** Ø 59 – schmaler Plattenring, zwei Wände aus normalen schwarzen Steinen (2 Lagen), Obergurt aus 2 Plattenlagen, hängt am Dach
14. **Scheinwerfer** – 24 hängende Lampen unter dem Truss, jeweils mit LED (siehe „LED-Beleuchtung“)
15. **Kettenzüge** – 8 Aufhängungen aus je 4 Rundsteinen 2 × 2 (3941) zwischen Truss und Decke
16. **Dach** 64 × 64 – Decke (Platten), Trägerrost (Steine), Dachplatten, umlaufende Attika

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

## Dach, Ecktürme und Truss-Aufhängung

Wie bei der echten Bühne hängt der Truss-Ring von oben. Unter dem Ring steht nichts mehr,
nur die vier Ecktürme ganz außen an der Baseplate:

| Bauteil | Aufbau |
|---|---|
| **Ecktürme** | 4 × 4 Noppen an jeder Ecke, 4 Ebenen aus je 4 Gitterträgern 95347 (hellgrau wie Alu-Traversen), zwischen den Ebenen Platten 4 × 4 als Verbinder. Höhe genau bis unter die Decke |
| **Decke** | Plattenlage 64 × 64 (große Platten 16 × 16 und 8 × 16, schwarz) |
| **Trägerrost** | 1 Stein hoch auf der Decke: Rand 2 Noppen breit, Träger alle ca. 8 Noppen in beiden Richtungen, massive Blöcke über den Türmen und Kettenzügen |
| **Dachplatten** | zweite Plattenlage 64 × 64 (dunkelgrau) – Decke, Rost und Dachplatten bilden eine steife Sandwich-Platte |
| **Attika** | umlaufender Randträger, 2 Noppen breit, 2 Steine hoch im Verband – versteift die Dachkanten zwischen den Türmen |
| **Kettenzüge** | 8 Aufhängungen (alle 45°) aus je 4 Rundsteinen 2 × 2 (3941), unten auf dem Obergurt des Truss, oben in der Decke |

Grob geschätzt wiegt das Dach ca. 1,5 kg und der hängende Truss mit Scheinwerfern ca. 0,6 kg.
Die 64 Gitterträger tragen das auf Druck problemlos. Die Kettenzüge und der Truss halten auf Zug
über die Klemmkraft der Noppen (je Kettenzug ca. 75 g).

**Aufbau-Reihenfolge:** Basis, Kuppel und Ecktürme bauen. Den Truss-Ring mit Scheinwerfern und
Kettenzügen fertig bauen und auf provisorische Stützen in der richtigen Höhe stellen (Oberkante
der Kettenzüge = Oberkante der Türme). Das fertige Dach von oben aufsetzen und gleichzeitig auf
Türme und Kettenzüge drücken, dann die Stützen entfernen.

| Dach von oben | Kabelausgang am Eckturm hinten rechts |
|---|---|
| ![Dach](renders/globe_stage_dach.png) | ![Kabelecke](renders/globe_stage_kabelecke.png) |

## LED-Beleuchtung

Beide Lichtquellen sind für echte LEDs vorbereitet und hängen an **einer** USB-Versorgung (5 V).
Beide Kabel kommen hinten aus dem Modell: das des LED-Streifens aus dem Kabeltunnel hinten Mitte,
das der Scheinwerfer am Eckturm hinten rechts.

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
| **Sammelleitung** | durch ein Loch im Obergurt in den Kettenzug hinten rechts. Die Rundsteine 3941 haben eine durchgehende Achsbohrung, darin läuft die Leitung nach oben |
| **Im Dach** | durch ein Loch in der Decke in einen Kabelkanal, der im Trägerrost ausgespart ist, bis zum hinteren Dachrand direkt neben dem Eckturm hinten rechts |
| **Anschluss** | am Eckturm entlang nach unten (im Gitter geführt oder mit kleinen Clips) und an der Ecke der Baseplate nach außen, wie die Kabel an echten Bühnentürmen |

**Statik:** Die Löcher sind einzelne Zellen in kreuzweise verbauten Plattenlagen; Truss und
Decke bleiben durchgehend verbunden. Der Generator prüft neben der Statik auch den Kabelweg:
Lampenlöcher frei, Obergurt-Loch über dem Kanal, Kabel-Kettenzug durchgehend aus 3941, Loch in
der Decke frei, Kabelkanal im Trägerrost frei bis zum Dachrand neben dem Turm, LED-Kanal und
Schacht leer.

**Einbau:** LEDs und Drähte einsetzen, bevor die Truss-Wände und der Obergurt aufgesetzt
werden. Die Sammelleitung durch den Kabel-Kettenzug ziehen, bevor das Dach aufgesetzt wird,
und dabei durch das Deckenloch in den Kabelkanal des Dachs führen.

| Truss-Kanal im Schnitt (Wände/Obergurt ausgeblendet) | Scheinwerfer von unten |
|---|---|
| ![Kanal](renders/truss_kanal_schnitt.png) | ![Unten](renders/globe_stage_scheinwerfer_unten.png) |

## Statik & Prüfung

Der Generator prüft das Modell nach jedem Lauf automatisch:

- **0 nicht verbundene Teile**: Jedes Teil hängt über Noppenverbindungen an der Baseplate.
- **0 schwebende Teile**: Jedes Teil sitzt auf mindestens einer Noppe. Die 216 Ausnahmen hängen mit Klemmkraft von oben: die Deckenplatten (am Trägerrost), Teile der unteren Truss-Plattenlage (kreuzweise unter der zweiten Lage verbaut) und die Scheinwerfer. Der Truss als Ganzes hängt über die Kettenzüge am Dach.
- **0 Kollisionen**: kein Volumen doppelt belegt
- Alle Steine liegen exakt im Noppenraster.

Die Renderings entstehen mit dem Headless-Renderer in [`../tools/ldraw-render`](../tools/ldraw-render)
(three.js LDrawLoader + Chromium, echte LDraw-Teilegeometrie).

## Neu erzeugen

```bash
pip install numpy global-land-mask     # Landmaske für das Erd-Mosaik
python3 globe-stage/generate_globe_stage.py
```

Alle Parameter (Kuppelprofil, Kartenmitte, Wolken, Kettenzug- und Lampenpositionen, Dachraster, Farben) stehen im Skript.

## Hinweise & Grenzen

- **Schräge Spotlight-Strahlen** aus der Skizze lassen sich nicht aus Steinen bauen. Stattdessen hängen 24 Scheinwerfer mit echten LEDs unter dem Truss.
- **Kosten** grob geschätzt 650–950 € über BrickLink (Cheese-Slopes und 1 × 1-Platten sind günstig). Die größten Posten sind:
  - 4 schwarze 32 × 32-Baseplates
  - 64 Gitterträger 95347
  - 29 große Platten 16 × 16 und 12 × 8 × 16 für das Dach
  - die rund 1.470 Cheese-Slopes der Kuppel
  - die schwarzen Kernsteine der Kuppel
