# Technik-Katalog

Jede Technik mit Zweck, Teilen und Stolperfallen. Teile-IDs sind LDraw-IDs (in LDraw geprüft);
BrickLink-Abweichungen stehen in `teile.md`.

## 1. SNOT (Studs Not On Top)

Zweck: glatte Fronten, Details in Wänden, Flächen in jeder Richtung, feinere Auflösung (Platte statt Stein).
- **Fliesenfront**: Wand aus 11211/30414/87087, davor Fliesen oder Platten → glatte, fugenarme Fassade.
- **Mauerverband seitlich**: 1x2-Fliesen hochkant auf Stud-Bricks = realistische Ziegel mit Fugen.
- **Gitter und Lautsprecher**: 2412b (Gitterfliese) auf 11211 → Lüftung, Boxen, Front-Fills.
- **Relief in ½-Platten-Stufen**: Headlight (4070) neben 87087 kombinieren (siehe `geometrie.md`).
- **Kern-Würfel**: 4733/47905/32952 als Knoten; darauf Paneele in alle Richtungen (Lowell-Kugel).
- **Seitliche Mosaike/Schriften**: Fliesen auf SNOT-Wand, Auflösung 1 Platte statt 1 Stein.
- Stolperfalle: Die 5:2-Mathe muss aufgehen, sonst entstehen Spalte oder Spannung.
- **SNOT-Wand als System**: Außenhaut → Seitennoppen → 1 Stein (3 Pl.) + 2 Platten Ausgleich → nächste
  Seitennoppen-Ebene → Kernwand. Tragende SNOT-Flächen aus langen Seitennoppen-Steinen (11211, 30414)
  statt vieler 1x1; ab 8 Studs Breite mindestens alle 8 Studs eine Verbindung zum Kern (Heuristik).
- **Stabilität nach Methode**: Seitennoppen-Steine sehr gut; Brackets gut, wenn beide Seiten eingebunden
  sind, als 1-Stud-Dekostreifen nur mittel; Clip/Stange neutral gut, unter Hebellast schwach;
  Technic-Pins sehr gut (erste Wahl für abnehmbare, transportfeste Module). Beleg im Set: 31109 Pirate Ship
  (SNOT-Rumpf), 10243 Parisian Restaurant (SNOT-Fassade).

## 2. Halbe-Noppe-Versatz

- Jumper 3794b/15573 (1x2), 87580 (2x2).
- Details mittig auf gerader Breite; Verjüngung um 1 Stud; Fugen versetzen; Fensterreihen zentrieren.

## 3. Winkel und Schrägen

- Pythagoras-Tripel (3-4-5 usw.), Scharnierplatten 2429c01, Drehteller 3680/3679, Rastscharniere
  44301a/44302a, Clip/Stange (Details in `geometrie.md`).
- Keilplatten (Wedges) 43722/43723 (2x3), 41769/41770 (2x4), 51739, 2450 (3x3 ohne Ecke),
  26601 (2x2 ohne Ecke) für schräge Kanten ohne Winkelbau.

## 4. Runde Formen

- **Stufenkreis + Kappen**: Ringe aus Steinen, jede freie Stufe mit Cheese (54200) oder Curved (11477)
  nach außen kappen → Umriss wirkt rund. Ringbreite so, dass man nicht in den Kern sieht.
- **Kurven-Fliesen und -Platten**: 25269 (1x1 Viertel), 27925 (2x2 Viertel), 30357 (3x3 mit Rundung),
  30565 (4x4 Viertel), 80015 (5x5 Makkaroni-Ring) → saubere Kurven in Draufsicht.
- **Runde Steine/Platten**: 3062b, 3941, 6141, 4032a, 14769 (2x2 Rundfliese), Kegel 4589/3942c.
- **Lowell-Kugel**: SNOT-Würfel mit Noppen in 6 Richtungen, 6 gleiche gewölbte Plattenpaneele.
- **Gebogene Wand**: Seitlich-und-oben-Technik (Despathens) – Innenradius ein Vielfaches von 5 Platten hoch.
- **Kuppeln**: Ring i reicht radial bis zum Außenradius von Ring i+1; oberste Lage volle Scheibe.
  Für eine glatte Silhouette den Durchmesser pro Ebene um höchstens 2 Studs verkleinern; Kappen aus
  Curved 3x2 (24309) oder 5093.
- **Fertige Kreise**: Rundplatten 4x4/6x6/8x8 (60474/11213/74611), Ring 4x4 (11833), Drehteller flach
  4x4 (61485) für drehbare Module.
- **Große Zylinder aus Scharnier-Ringen** (Hinge 3937/6134 oder Scharnierplatten): erst ab ca. 12 Studs
  Durchmesser sinnvoll, ab 16 Studs erste Wahl; gerader Durchmesser, zwei Ringe als Doppellage, Innen ein
  Steinkern, etwa alle 8 Studs Höhe eine Querplatte zur Versteifung, außen mit Platten/Fliesen verkleiden.
  Unter 12 Studs lieber Stufenkreis mit Kappen (oben).
- Tabu: Platten/Wände biegen, um Kreise zu erzwingen (Spannung).

## 5. Rockwork (Fels, Berge, Klippen)

- **Slopes UND umgedrehte Slopes mischen** (3040b/3665a, 3039/3660a): echte Überhänge statt Böschung.
- **Winkel mischen**: 18° (60477), 33° (4286/3298), 45° (3040b/3039), 65° (60481), 75° (4460b) – je
  steiler die Stufe, desto steiler das Teil. Gleichmäßige Steigung = durchgehend gleiches Teil
  (z. B. Grat aus 65°-Slopes, Rampe aus 18°-Slopes in Linie).
- **Keine Muster**: Platzierung von Kappen, Überhängen, Farbflecken per glatter Rauschfunktion, nicht
  pro Zelle zufällig und nicht im Raster.
- **Schichten**: untere Lagen weiter vorne; Schichtfugen horizontal, Risse als 1 Stein tiefe Kerben in
  Dunkelgrau.
- **Erosion**: Kanten gemischt aus Curved 11477 und Cheese 54200 → ausgewaschen statt treppig.
- **Licht-Schattierung**: Farbe nach Normalen·Lichtrichtung (zugewandt hell, abgewandt dunkler), dazu
  ein Höhenverlauf (Spitze hell, Fuß dunkel).
- **Senkrechte Riefen**: Wandfarbe nur von der Position entlang der Wand abhängig machen (Streifen in
  Weiß/Hellgrau/Dunkelgrau) – oder Riffelsteine 2877 (Rillenseite im Render prüfen).
- **Wege in Flanken**: bergseitig Wand + Schulter (≥ Weghöhe + 1 Stein, 2–3 Zellen tief),
  talseitig höchstens Weghöhe; Mulden hinter Wegkanten auffüllen.
- Farbfamilien: Grau (LBG/DBG), Sand (Tan/Dark Tan), dazu Olivgrün/Dunkelgrün als Moos.
- **Ablauf** für eine Felsmasse: Silhouette als Umriss → in 2–6 große Massen teilen → jede Masse mit
  stabilem Kern → Außenhaut aus unterschiedlich ausgerichteten 1x1-/2x1-Slopes → Farbe in drei Stufen
  (Grundton, Schatten, wenige Lichter).
- **Prüfregeln (Heuristik)**: nicht mehr als 3 gleiche Slope-Typen direkt nebeneinander; keine
  perfekt waagerechte Felskante über 4 Studs; mindestens ein Facettenwechsel pro 2–4 Studs Sichtfläche;
  Farbwechsel entlang der „Geologie“ (Schichten, Risse), nicht fleckig.
- **Dunkler Bühnenfels (nicht Yeezus, dort rein unbunt)**: etwa 40–60 % DBG, 15–25 % Schwarz,
  10–20 % Dark Tan/Reddish Brown, 5–15 % dunkle Grüntöne – wenige Erdtöne lesen sich besser als viele
  gesättigte Farben.

## 6. Wasser

- Trans-Clear/Trans-Light-Blue-Fliesen über dunklen Platten; einzelne Noppen frei lassen = Wellen.
- Flachwasser: Trans-Light-Blue über Dark Tan; Tiefe durch dunkleren Untergrund.
- Wasserfall: gestapelte 1x1-Rundplatten (6141) in Trans-Clear/Weiß, oder SNOT senkrecht.
- Schaum/Gischt: weiße Rundfliesen 98138 und 1x1-Rundplatten an Felskanten.
- Ruhiges Wasser: über 70 % der Fläche auf einer Fliesenebene; bewegtes Wasser: 20–40 % Höhen- oder
  Richtungswechsel; Wellen als gerichtete Gruppen von 2–6 Studs, nie einzeln zufällig (Heuristik).

## 7. Vegetation

- Blätter 2423, 1x1-Rundplatte mit Blättern 32607, Blüte 33291; Äste aus Stangen + Clips.
- Laub mit Wedges und 1x1-Rundplatten „strecken" (volle Form mit wenig Teilen).
- Mehrere Grüntöne mischen (Grün, Dunkelgrün, Olivgrün, Lime als Licht).
- Stämme aus runden Steinen (3062b/3941) in Braun, Wurzeln aus Slopes.

## 8. Oberflächen und Texturen

- **Verband**: Fugen von Lage zu Lage versetzt (Generator: Packachse pro Lage wechseln).
- **Dielen im Verband**: 1 Noppe breite Fliesen in Laufrichtung, Stöße versetzt (Laufsteg, Böden).
- **Mauerwerk**: 98283 (1x2 mit Ziegelprägung), 15533 (1x4), Fugen aus hellgrauen Platten zwischen
  Ziegellagen; Log-Stein 30136 für Holz.
- **Nieten und Paneele**: 6141 als Nieten, Cheese-Slopes als Paneelkanten, Fugen zwischen Fliesen.
- **Kopfsteinpflaster**: Mix aus 98138, 25269, 3070b in 2–3 Grautönen, einzelne Noppen frei.
- **Glatt vs. genoppt bewusst einsetzen**: Fliesen für „fertig/modern", Noppen als Textur (Gras, Fels).
- **Beton**: etwa 70–80 % glatte Fläche, 15–25 % Fugen/Plattenwechsel, 5–10 % Technikdetails; Fugen
  folgen einer plausiblen Bauweise (Schalungsraster), sonst wirkt es wie zufälliges graues Greebling.
- **Holz**: lange Streifen 1x2–1x8, Stöße um 1–3 Studs versetzt, nie 4 Stöße übereinander.

## 9. Greebling (mechanische Details)

- Viele kleine Teile, 1–2 Farben (meist DBG/LBG/Schwarz) + höchstens ein Akzent.
- Teile: Clips 4085c/61252, Gitterfliesen 2412b, 6141, Kegel 4589, 3062b, Stangen, Zahnplatten 49668,
  Griffplatten 60478/48336, Technic-Pins in Löchern.
- Zweck vor Menge: Greebles gehören an Maschinen, Technikzonen, Rückseiten – nicht gleichmäßig überall.
- Jedes Detail braucht eine Funktion, die man benennen kann: Paneelfuge, Lüftung, Halterung,
  Kabelanker, Wartungsklappe, Rohr, Licht, Schraube/Niete, Rippe. Ein Detail, das weder Silhouette noch
  Material noch Funktion verbessert, wird nicht erzeugt.

## 10. Mikromaßstab

- Wände 1 Platte oder 1 Stein dick; Fenster nur als Farbwechsel (Reihe Fliesen in Trans/Hellblau).
- Details über Farbwechsel und SNOT-Fliesen statt Öffnungen; Jumper für Symmetrie.
- „Wenn es richtig aussieht, ist es richtig" – Proportion schlägt Maßtreue.
- Bühnen-Maßstab dieses Projekts: Mikro (1 Stud ≈ 0,5–1 m), Figuren weglassen.

## 11. Licht und Elektrik

- LEDs in Hohlnoppen, Technic-Löchern oder unter Trans-Teilen (6141, 3062b, 4589 in Trans-Clear).
- LED-Streifen auf 1x6-Platten kleben, in einen Kanal aus Steinen mit Fliesendeckel legen.
- Kabel in Fugen, unter Fliesen, durch Treppenhäuser/Türen führen; Statik neu prüfen, wenn Streifen
  tragende Teile ersetzen (Globe Stage: Ring-Kanal statt gebauter LED-Imitation).
- Mini-LEDs mit sehr dünnen Drähten lassen sich nachträglich fast unsichtbar verlegen. Kabelkanal
  mindestens 1 Stud breit, Wartungszugang etwa alle 16–24 Studs, keine Leitung durch tragende
  Scharnier-/Pin-Zonen (Heuristik).

## 12. Bühnen- und Showtechnik (aus diesem Repo)

- **Traversen**: Gitterträger 95347 gestapelt (DBG tritt optisch zurück), Plattenlagen per
  Verbund-Algorithmus zu einem Stück verbinden, Pfosten 3062b im Zickzack.
- **Abhängen**: Schnur mit Endnoppen 63142 statt massiver Stützen; Last über Schlingen, im Check als
  Verbindung modellieren. Variante J-Bogen: unterer Knopf von unten in den Endblock eines Trägers (Saint Pablo).
- **Runde Köpfe mit Cartoon-Gesicht (4x4)**: 3 Steinlagen + Platte 4x4 + Kuppel 4x4 (86500 glatt / 30208 facettiert).
  Vorne SNOT: Grinsen = 30414 + Fliese 1x4 schwarz, Nase = 11211 + Cheese-Slope 85984 mit Unterseite an der Wand
  (kragt nach unten aus), Augen = zwei Headlight-Steine 4070 (gemeisselte Hoehle, Noppe = Pupille; KEINE
  bedruckten Kulleraugen - vom Nutzer abgelehnt), Mund als dunkelgraue Rille statt schwarzem Band; Ohren = Rundfliese 2x2
  (14769) mittig auf einer Seitennoppe (87087). Eckige Front wirkt cartoonhaft, runde Eck-Steine (3062b) dagegen
  technisch ("Rohre"). Fels vor und neben dem Kopf absenken, sonst kollidieren Ohren mit Slopes (Circus Maximus).
- **Rockwork-Details nach Prioritaet verteilen**: Spitzen (3062b + Kegel 4589), Felskugeln (30367c/30151b), Glut
  (Rundfliese Trans-Orange), Felsspots, Reliefgesichter (4070-Augen + 3040b-Nase + Fliesen-Mund) VOR den
  Kanten-Slopes vergeben, sonst belegen Curved/Cheese alle Oberseiten. Treppen direkt ins Hoehenfeld schneiden.
- **Lichtraster**: Rundsteine 1x1 (3062b) in Ketten unter ein Plattengitter hängen, unten Rundplatte Trans-Orange;
  im Zickzack entlang der Balken, in der Mitte länger. Leuchtet erst im Konzert-Render (Emission + Dunst).
- **Line-Arrays**: Boxen aus 11211 + 3004 + Gitterfliese (SNOT), J-förmig gekrümmt.
- **Moving Heads**: 3022 + 3941 + 4032a in Trans-Clear (echte LED möglich).
- **Screens**: Stein-Mosaik mit farbbewusster Aufteilung; Umriss mit Curved/Cheese gerundet;
  Rückseite schwarz; an der Traverse aufhängen.
- **Podest**: schwarze Blöcke, Kante mit DBG-Fliesen, Front-Fills als SNOT-Gitter.
- **Truss in Mikro-Bauweise** (Alternative zu 95347): Modul 4 Studs aus Ober-/Untergurt und zwei
  Diagonalen (Stangen 87994, Rundplatte mit Stange 32828, Clip-Fliesen 2555/15712); frei tragend immer
  zwei parallele Lastpfade, über 8 Studs Spannweite eine zweite Auflage.
- **Line-Arrays**: 1–2 Studs breite Module, 4–8 Wiederholungen, geometrisch exakt gleich – nur Winkel
  und Abstand zur Bühne ändern sich.
- **LED-Wand**: sichtbare Pixel aus 1x1 (Rundfliese 98138 für Mikro-LEDs), reine schwarze Screen-Fläche
  aus 2x2/2x4-Fliesen (3068b/87079).
- **Nebel** in Trans-Clear/Weiß als 3–7 versetzte Volumen-Cluster, nie als kompakte Kugel; **Pyro/CO2**
  radial oder senkrecht an der technischen Quelle verankern, nicht als verstreute Trans-Teile.
- **Publikum ohne Minifiguren**: 1x1-Rundplatten, Rundfliesen und Platten in 2–4 dunklen Farben; vorne
  dicht, Mitte mittel, hinten locker (Dichteverlauf gibt Tiefe).
- Beleg für Bühnenbau im Set: 41714 Andrea's Theatre School; Community-Bühnen z. B. Pink-Floyd-MOCs auf
  Rebrickable (MOC-140474, MOC-197154).

## 13. Mosaike

- 1x1-Fliesen oder Rundfliesen; Motivränder und Schrift gezielt setzen, nur das Innere samplen.
- Varianten erzeugen und gegen die Vorlage bewerten (ΔL\* aus Distanz, SSIM im Detail):
  `tools/mosaic/make_mosaic.py`.
- Feste Stückzahlen je Farbe: Zellen nach Helligkeit sortieren, per Quantilen zuteilen.
- Spiegelung prüfen (Korrelation Render ↔ Vorlage), bevor das Mosaik verbaut wird.
- **Farbabstand** in Lab messen, am besten mit CIEDE2000 (wahrnehmungsnäher als RGB-Abstand); erst
  Helligkeit (Y = 0,2126 R + 0,7152 G + 0,0722 B, linear) treffen, dann den Farbton.
- **Dithering** (Fehlerdiffusion) lohnt bei Betrachtung ab etwa 1 m (Haut, Himmel, Grauverläufe,
  Gemälde); für Nahbetrachtung unter 30 cm reduzieren. Gesichter: Helligkeit vor Sättigung.
- **Palettengröße**: grafisch 6–10 Farben, fotorealistisch 10–18, maximale Farbtreue 18–30 – mehr Farben
  erzeugen schnell Rauschen; Verfügbarkeit jeder Farbe vorher prüfen (fehlende Farben kippen die Planung).
- Teilewahl: 3024 stark genoppt (grob/technisch), 6141 punktuell mit leichter Tiefe (LEGO-Art-Look),
  98138 glatt (Fotomosaik), 3068b/87079 für ruhige Flächen, 54200 für Richtung/Pinselstrich.
- Größe: 96×96 = 9.216 Pixel ≈ 77 cm, 128×128 = 16.384 Pixel ≈ 102 cm. Belege im Set: 31205 Jim Lee
  Batman (großes 1x1-Mosaik), 31206 The Rolling Stones (Mosaik mit zusätzlicher Tiefe/Layering).

## 14. Farbverläufe und Alterung

- Verlauf über Zwischenstufen (Weiß → LBG → DBG → Schwarz) mit Rausch-Übergang statt harter Linie.
- Alterung: einzelne Steine in Nachbarfarbe (Dark Tan in Tan, DBG in LBG), bevorzugt unten und an
  Kanten, wo Wasser läuft.

## 15. Relief-Mosaik („Chaos-Pixel-Art", Stil mbrick_art)

Wandbild aus lauter gemischten Einzelteilen, Noppen zum Betrachter. Aus der Entfernung liest man das Motiv
(z. B. den Porsche 911 von mbrick_art, „über 7.500 Pixel"), aus der Nähe eine wilde Textur aus Rundsteinen,
Kegeln, Technic-Steinen, Gittern, Slopes und Blüten.

Regeln, die den Stil ausmachen:
- **1 Noppe = 1 Pixel**, aber jede Zelle hat ein **anderes Abschlussteil** und eine **andere Höhe** (0–3 Platten + Teil).
  Die Tiefe erzeugt Schatten und macht das Bild lebendig; Hohlnoppen, Löcher und Kegel geben Mikrotextur.
- **Farbe zuerst nach Helligkeit**: Pixel auf die nächste Palettenfarbe (Lab) abbilden. Ein Teil der Zellen bekommt
  die zweitnächste Farbe („Chaos") – so entstehen Mischflächen statt glatter Farbfelder.
- **Konfetti**: ein paar Prozent Zellen in bunten Akzentfarben (Lila, Lime, Pink, Azur, Orange) mit **gleicher
  Helligkeit** wie das Originalpixel. Im Detail farbig, aus der Entfernung stört es das Motiv nicht.
- **Mitunter größere Teile**: benachbarte gleichfarbige Zellen gleicher Höhe teils als 1×2 (Stein, Technic-Stein,
  Gitter, Cheese 1×2, Jumper) oder 2×2 (Rundstein, Rundplatte) – bricht das Raster auf.
- **Lichtpunkte** (Scheinwerfer, Blinker): helle, gesättigte Farben (Orange, Gelb) gezielt, gern etwas höher.
- **Motiv-Kontur**: dunkles Motiv vor hellem Grund – der Rand darf ausfransen (Teile stehen einzeln über).
- **Aufbau real**: auf Baseplates, oder auf Platten mit Rahmen; Motiv-Rand bei Freiform-Bildern ohne Grundplatte
  direkt an die Wand (dann Platten-Unterbau im Verbund).

- **Z-Achse als Gestaltungsmittel**: Hintergrund flach (0–4 Platten, helle Stellen höher = Wolken), Motive als Kuppeln
  oder Plateaus 8–15 Platten hoch. Höhen über 3 Platten als 1×1-Steine stapeln (weniger Teile).
- **Bedeutung durch Teilewahl** („Nice Part Usage"): Ringe mit Satellitenschüsseln besetzen, Augen als Radar-Schüssel,
  Explosionen aus Kegeln und Doppel-Slopes, Blumenfelder aus Blumen 2×2 und Blütenplatten, Schrift aus glatten Fliesen
  auf genopptem Grund. Pro Bildteil eine Zone mit eigenem Teile-Pool.

- **Wie ein Maler** (Beispiel MBDTF): Pinselstriche aus langen 1×2–1×4-Teilen in Strichrichtung; Licht von links oben
  als Farbstufe gleichen Farbtons (Schwarz nie aufhellen, Hintergrund nur Schatten → Schlagschatten des Rahmens);
  Slopes folgen dem Gefälle; Motiv-Umriss aus nach außen fallenden Slopes; Motiv ohne Konfetti; Gesichtszüge als
  handgesetzte Einzelteile (weiße Rundplatte mit offener Noppe = Auge mit Pupille).

- **Tiefe semantisch staffeln**: höchstens 4–5 Tiefenklassen (0 / +1 / +2 / +3 / +4 Platten bzw. die
  Zonen-Höhen), nicht jede Form eine eigene Höhe. Aufbau von hinten nach vorn: Grundplatte → Rahmen →
  Mosaikfeld → ausgewählte Erhebungen → Hauptobjekt.
- **Pinselstriche** als gerichtete Gruppen (gleiche Richtung über 3–5 Zellen), nie zufällig.
- **Rahmen** 3–5 Studs breit, Außenkante Fliesen, Unterbau Stein/Platte im Verbund; der Rahmen muss das
  Relief in beiden Richtungen koppeln, nicht nur dekorativ aufsitzen.

Werkzeug: `tools/relief/make_relief.py bild.jpg ausgabe/name --breite 48 --hoehe 48 --chaos 0.35 --konfetti 0.05`
(MPD, Stückliste, BrickLink-XML, flache Farbvorschau). Für Wandbilder frontal von oben rendern
(`[0,88,1.0,0,-20,0,30]`) plus eine flache Schrägansicht für die Tiefe.
