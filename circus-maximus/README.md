# Travis Scott – Circus Maximus Tour (UTOPIA-Bühne) als LEGO-MOC

Nachbau der Arena-Bühne der Circus-Maximus-Tour (Album *UTOPIA*, 2023–2025) auf **zwei Baseplates 32 × 32**
(64 × 32 Noppen, ca. 51 × 26 cm). Wie auf den Bühnen-Renderings windet sich ein **schmaler Weg durch die
Halle**, beidseitig von grauen, verwitterten Felswänden und **Findlingen mit Gesichtern** gesäumt. An einem Ende
steht ein **hoher Felsblock mit eingemeißelten Gesichtern und einem Durchgang**, oben eine Plattform für den
Performer (wie auf dem Stadionfoto). Über der Bühne hängen ein **ovaler 360°-Videoring**, **fliegende Köpfe mit
Glotzaugen**, Scheinwerfer und die PA an einem Traversen-Raster. Das Publikum steht rundherum.

![Hero](renders/cm_hero.png)

| Felsblock mit Gesicht und Durchgang | Gewundener Weg mit Findlingen |
|---|---|
| ![Block](renders/cm_block.png) | ![Pfad](renders/cm_pfad.png) |

| Von oben: Grundriss des Weges | Köpfe unter dem Videoring | Blick entlang der Bühne |
|---|---|---|
| ![Oben](renders/cm_oben.png) | ![Köpfe](renders/cm_koepfe.png) | ![Stirnseite](renders/cm_stirnseite.png) |

![Seite](renders/cm_seite.png)

## Kennzahlen

- **2.790 Teile**, 105 Positionen (Teil × Farbe), keine Minifiguren
- **Grundfläche** 64 × 32 Noppen, **Höhe** ca. 36 cm
- **Weg** 56 Noppen lang, Felsblock 12 Steine hoch
- **Videoring** Oval 54 × 25 Noppen, 4 Steine hoch, an 20 Seilen

## Vorlage

- **Bühnen-Renderings** (Ansichten und Grundriss): langer, schmaler, gewundener Weg mit Zickzack in der Mitte,
  Felswände und runde Findlinge mit Gesichtern am Rand, an einem Ende ein hoher Block mit Gesichtern und Durchgang
- **Probenfoto in der Arena**: graue Felswände etwa doppelt mannshoch, runder Steinkopf mit großen Augen am
  Traversen-Raster, viele Scheinwerfer und PA-Hänge
- **Stadionfoto**: hoher Fels mit eingemeißeltem Gesicht, Travis Scott oben auf dem Gipfel
- Beschreibungen der Produktion: 360°-Videoring, 13 fliegende Köpfe (2–4 m breit), Felsen mit strukturierter Beschichtung

## Aufbau (Submodelle)

1. **Grundplatten** – 2 × Baseplate 32 × 32 schwarz
2. **Felswände und Findlinge** – grauer Stein (Dunkelgrau, im Licht Hellgrau, Schwarz in Spalten), Slopes an jeder
   Stufe, Überhänge auf umgedrehten Slopes, Kanten aus gebogenen Slopes und Cheese-Slopes; 5 Findlinge als runde Kuppen
3. **Gewundener Laufweg** – 4 Noppen breit, schwarze Dielen im Verband, folgt der Zickzack-Linie aus dem Grundriss,
   Stufen an beiden Enden
4. **Plattform auf dem Block** – Performer-Fläche, Rand hellgrau
5. **Hoher Felsblock mit Durchgang** – 12 Steine hoch; der Weg führt unter 8 Bögen 1 × 6 × 2 hindurch
6. **Gesichter (SNOT)** – Augen aus Headlight-Steinen mit runden Fliesen auf der Seitennoppe, Mund aus einer
   Gitterfliese auf einem Stein mit Seitennoppen; am Block beidseitig, an den Findlingen zur Halle
7. **Ovaler Videoring** – 2 Noppen dick, 4 Steine hoch, Graustufen-Bildinhalt, hängt an 20 dünnen Seilen
8. **Türme und Traversen-Raster** – 6 Gittertürme (95347), Außenrahmen plus 5 Quertraversen
9. **Fliegende Köpfe** – 5 Köpfe (einer groß in der Mitte): runder Schädel aus Cheese-Slopes, Glotzaugen aus
   Headlight + weißer Rundfliese, Nase als 45°-Slope, dunkler Mund
10. **PA-Hänge** – 8 Stränge an den Längstraversen, Lautsprechergitter per SNOT nach außen
11. **Moving Heads** – 23 Scheinwerfer an den Quertraversen

## Angewandte Techniken (Skill `lego-profi-designer`)

| Technik | Umsetzung |
|---|---|
| **Grundriss aus der Vorlage** | Die Mittellinie des Weges ist als Polylinie aus dem Grundriss-Rendering übernommen, Felswände folgen ihr beidseitig |
| **SNOT-Gesichter** | Headlight-Stein (4070) + runde Fliese 1 × 1 = rundes Auge mit ½-Platten-Relief; Gitterfliese auf 11211 = Mund |
| **Bögen als Tunnel** | Bögen 1 × 6 × 2 überspannen den Weg im Block, die Felswände darüber sitzen auf den Noppen der Bögen |
| **Rockwork** | Slopes nach Stufenhöhe, Überhänge auf umgedrehten Slopes, erodierte Kanten, Schattierung nach Lichtrichtung |
| **Helligkeitsstufen** | Grauer Stein in drei Stufen, schwarzer Weg als Kontrast, weiße Augen der Köpfe als hellster Punkt |
| **Dünne Aufhängung** | Ring, Köpfe und Scheinwerfer hängen an Säulen aus runden Steinen/Platten – liest sich als Seil |
| **Verband über Treppenecken** | Der ovale Ring ist 2 Noppen dick, damit die Lagen an den Diagonalen verbunden bleiben |

## Prüfung

Der Generator prüft nach jedem Lauf: **0 nicht verbundene Teile, 0 schwebende Teile, 0 Kollisionen**.
Hängende Teile (Ring, Seile, Köpfe, PA, Scheinwerfer, untere Traversenlage) halten mit Klemmkraft von oben;
Augen, Münder und Lautsprechergitter sitzen per SNOT an ihren Haltern.

## Neu erzeugen

```bash
python3 circus-maximus/generate_circus_maximus.py
```

## Hinweise

- **Arena- und Stadionversion gemischt:** Der hohe Block mit Gesicht und Gipfel stammt aus der Stadionversion,
  der gewundene Weg und das Raster aus der Arena-Version.
- **Spiral-Auge:** Das eingemeißelte Spiral-Auge lässt sich im Mikromaßstab nicht darstellen; es ist ein rundes Auge.
- **Videoring:** Auf den Fotos nicht sichtbar, Form und Lage stammen aus den Produktionsbeschreibungen.
- **Gitterträger in Dunkelgrau** (95347) sind seltener als in Hellgrau – Verfügbarkeit auf BrickLink prüfen.
