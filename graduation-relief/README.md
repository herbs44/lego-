# Kanye West – Graduation als LEGO-Relief

Das Albumcover *Graduation* (2007, Artwork von Takashi Murakami) als Relief-Mosaik im Stil von LEGO-Wandkunst
(mbrick_art): **96 × 96 Noppen** (ca. 77 × 77 cm) auf 4 Baseplates 48 × 48, **25.181 Teile** in 30 Farben.
Jede Noppe ist ein Pixel, aber jedes Pixel ist ein anderes Teil in anderer Höhe – aus der Entfernung das Cover,
aus der Nähe eine wilde Textur aus Rundsteinen, Kegeln, Technic-Steinen, Gittern und Blüten.

| Frontal (wie an der Wand) | Schräg |
|---|---|
| ![Front](graduation_front.png) | ![Schräg](graduation_schraeg.png) |

| Dropout-Bär im Himmel | Stadt unten rechts | Oberer Rand mit Titelband |
|---|---|---|
| ![Bär](graduation_baer.png) | ![Nah](graduation_nah.png) | ![Titel](graduation_schrift.png) |

![Farbvorschau](graduation_relief_vorschau.png)

## Dateien

- `graduation_relief.mpd` – Modell (Noppen nach oben = zum Betrachter; zum Aufhängen hochkant drehen)
- `graduation_relief_bom.csv`, `graduation_relief_bricklink.xml` – Stückliste und BrickLink-Wanted-List
- `graduation_relief_vorschau.png` – flache Farbvorschau (1 Pixel = 1 Noppe)

## Neu erzeugen

```bash
python3 tools/relief/make_relief.py cover.jpg graduation-relief/graduation_relief --breite 96 --hoehe 96 --chaos 0.22 --konfetti 0.035 --seed 3
```

Das Cover-Bild selbst liegt nicht im Repo (Urheberrecht); das Skript braucht es als Eingabe.

## Hinweise

- **Farben:** Der Himmel nutzt Magenta, Dark Pink, Bright Pink, Lavender, Medium Lavender, Dark Purple und Coral.
  Einige davon sind bei bestimmten Teilen (z. B. Kegel, Blüte) selten – BrickLink-Verfügbarkeit prüfen oder dort auf
  Rundplatten ausweichen (`--seed` ändern verteilt die Teile neu).
- **Schrift:** Auch bei 96 Noppen ist „Kanye West GRADUATION" nur ein helles Band – die Buchstaben sind im Cover kleiner als
  2 Noppen. Lesbar wird sie nur als eigens gesetzter Schriftzug (z. B. SNOT-Fliesen) oder mit einem hochauflösenden Cover
  ab ca. 128 Noppen Breite.
