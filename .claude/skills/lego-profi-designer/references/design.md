# Design-Prinzipien (Profi-Niveau)

## 1. Silhouette und Geste zuerst

- Ein gutes Modell ist an seinem Umriss erkennbar – auch einfarbig, auch klein.
- Vor jedem Detail: Massenmodell rendern (vorne, Seite, 3/4 von oben) und neben die Vorlage legen.
- Charakteristische Merkmale übertreiben statt verwässern (z. B. Grat des Bergs, runder Screen).
- Achsen und Symmetrien der Vorlage exakt treffen (Laufsteg genau auf der Mittelachse); natürliche
  Formen dagegen bewusst asymmetrisch.
- Reihenfolge: Silhouette → Massen → Architektur → Primärdetails → Sekundärdetails → Mikrodetails.
  Mikrodetails erst, wenn Silhouette und Massen im Render bestehen.

## 2. Maßstab und Proportion

- Leitmaß festlegen und durchhalten: Minifig (~1:40), Miniland (~1:20), Mikro (1:200 und kleiner).
- Proportionen aus der Vorlage als Verhältnisse messen (Höhe:Breite, Abstände) und auf das Raster
  runden. Bei Konflikt gewinnt die Wirkung, nicht der Millimeter.
- Im Mikromaßstab wird zu breit/zu hoch schnell sichtbar – SNOT (Plattenauflösung) und Jumper
  (½ Stud) als Feinregler.
- **Ein Leitmaß, ein Modul**: z. B. Screen = 16 Studs, alles andere daraus ableiten; Bühnenelemente in
  einem Modul von 4 oder 8 Studs (Truss 4, LED-Segment 4/8, Line-Array 2/4, Bodenplatten 2/4,
  Felsfacetten 2/4/8) – so bleibt die Bühne parametrisch.
- **Forced Perspective** (Richtwerte): vorne 100 %, Mitte 85–90 %, hinten 70–80 %, Hintergrund 50–65 %;
  wirkt bei Laufstegen, Publikum, Traversen, Hintergrundbauten und Lichtstrahlen.

## 3. Farbe

- **Palette begrenzen**: 3–5 Farben plus Neutrale. **60-30-10**: Hauptfarbe, Nebenfarbe, Akzent.
- **Helligkeit vor Farbton**: Erst die Hell-Dunkel-Staffelung lesbar machen (Schwarzweiß-Test des
  Renders), dann Farbtöne wählen. Blickpunkt = stärkster Helligkeitskontrast.
- Große Strukturen, die zurücktreten sollen (Traversen, Rückwände), dunkler und entsättigt (DBG statt LBG).
- Schwarz schluckt Details im Foto – für sichtbare Detailflächen lieber DBG, Schwarz für Kern,
  Bühnenboden und Rahmen.
- Komplementärkontraste (Blau/Orange, Rot/Grün) nur als gezielter Akzent.
- Verfügbarkeit: Teil-Farb-Kombination muss bei BrickLink existieren; seltene Kombinationen vermeiden
  oder im README kennzeichnen.

## 4. Komposition und Blickführung

- Ein klarer Blickpunkt (Focal Point); alles andere ordnet sich unter.
- Linien führen zum Blickpunkt (Laufsteg → Berg → Screen).
- Staffelung Vorder-, Mittel-, Hintergrund; Überschneidungen erzeugen Tiefe.
- Forced Perspective: hinten kleinerer Maßstab, funktioniert nur aus einer Blickrichtung.
- Negativraum bewusst lassen (freie Sichtachse, Mitte der Traverse offen).

## 5. Detailhierarchie und Textur

- Detaildichte am Blickpunkt am höchsten, Ruhezonen daneben – gleichmäßige Details wirken wie Rauschen.
- Texturkontrast: glatt (Fliesen) ↔ genoppt ↔ strukturiert (Gitter, Mauerwerk, Riefen).
- Wiederholung vermeiden, wo die Natur keine hat (Fels, Pflanzen); Wiederholung nutzen, wo Technik
  sie hat (Traversen, Boxen, Fenster).
- „Nice Part Usage": ungewöhnliche Teile für neue Zwecke – sparsam und so, dass es passt.
- **Drei Detailgrößen**: Makro 8–32 Studs (Fels, Dach, LED-Wand, Laufsteg), Mittel 2–8 Studs (Lampen,
  Truss-Felder, Türen, Boxen), Mikro 1–2 Studs (Kabelhalter, Pixel, Nieten, Nebel). Mikrodetails dürfen
  Makroformen nie optisch zerlegen.
- **Ruhezonen**: 20–40 % einer großen Displayfläche bewusst ruhig lassen (Bühnenboden, Backstage).

## 6. Geschichte und Präsentation

- Was erzählt das Modell? (Performer auf dem Gipfel, Chor auf dem Sims). Ein Moment, klar lesbar.
- Präsentationsbasis mit sauberer Kante (Fliesen), ggf. Schild.
- Standard-Ansichten festlegen und für alle Iterationen gleich rendern (Vergleichbarkeit).

## 7. Baubarkeit und Kosten

- Bauabschnitte = Submodelle (Grundplatte, Podest, Berg, Weg, …); jeder Schritt baubar und verbunden.
- Unsichtbares Inneres billig (große schwarze Steine), sichtbare Flächen hochwertig.
- Teilezahl, Positionen (Teil × Farbe) und teure/seltene Teile im README nennen.
- Anleitung: pro Schritt wenige neue Teile, gute Sicht auf neue Teile, Teilaufbauten als Unterschritte.

## 8. Kritik-Methode (nach jedem Render)

1. Schwarzweiß-Blick: Ist die Hell-Dunkel-Staffelung klar? Wo ist der Blickpunkt?
2. Silhouette: stimmt sie aus allen Standardansichten mit der Vorlage?
3. Proportion: was ist zu groß, zu klein, zu breit? Welche Maße lassen sich um 1 Stud korrigieren?
4. Oberflächen: wo wirkt es kastig, flach oder verrauscht? Welche Technik aus `techniken.md` hilft?
5. Lesbarkeit der Funktion: erkennt man Wege, Treppen, Öffnungen, Technik?
6. Nutzerwunsch: ist jede Bitte sichtbar umgesetzt? Mehrdeutiges in beiden Lesarten prüfen.
Befunde als Liste mit konkreter Maßnahme (Teil, Ort, Zahl) formulieren, dann umsetzen und neu rendern.

Drei Prüfabstände: **1 m** (Silhouette, Hauptfarben, Hierarchie, große Formen, Lichtquellen),
**30 cm** (SNOT, Fugen, Wiederholungen, Kabel, Mikrodetails) und **einfarbig grau** gerendert – funktioniert
die Form ohne Farbe nicht, ist die Farbe nur Kosmetik.

## 9. Präsentation

- Sockel sichtbar breiter als die Grundplatte: 34–36 Studs bei 32×32, 50–52 Studs bei 48×48.
- Licht: Haupt-, Füll-, Akzent- und „praktisches“ Licht (eingebaute LEDs); bei Bühnen Frontlicht,
  Gegenlicht, Screen-Leuchten, Strahlen, Bodenlicht.
