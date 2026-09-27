# lego-

LEGO-MOCs als LDraw-Dateien (`.mpd`) mit Stückliste und BrickLink-Wanted-List.

## Modelle

| Modell | Teile | Beschreibung |
|---|---|---|
| [Yeezus Stage](yeezus-stage/) | 2.004 | Mount Yeezus: Fels-Pyramide vor dem runden Screen, Laufsteg zur Lower Stage im Publikum, Line-Arrays und Moving Heads – auf 2 Baseplates |
| [Globe Stage](globe-stage/) | 10.876 | Stadion-Konzertbühne mit gerundeter Erdkugel-Kuppel, echter LED-Beleuchtung (Ring + 24 Scheinwerfer), einem Truss-Ring an Seilen unter einem Dach auf vier schlanken Ecktürmen und dem Album-Cover als Dach-Mosaik |

![Globe Stage](globe-stage/renders/globe_stage_hero.png)

Bauanleitung als PDF: [`globe-stage/Bauanleitung_Globe_Stage.pdf`](globe-stage/Bauanleitung_Globe_Stage.pdf)

![Yeezus Stage](yeezus-stage/renders/yeezus_hero.png)

## Werkzeuge

- [`tools/mosaic`](tools/mosaic/make_mosaic.py) – Mosaik-Generator für 1 × 1-Fliesen: erzeugt mehrere Varianten und bewertet sie gegen die Vorlage (ΔL\* aus Abstand, SSIM im Detail).
- [`tools/ldraw-render`](tools/ldraw-render/) – Headless-Renderer für LDraw/MPD (three.js + Chromium) und
  `ldbbox.py` zum Nachschlagen von Teil-Abmessungen und Ursprüngen.
