# lego-

LEGO-MOCs als LDraw-Dateien (`.mpd`) mit Stückliste und BrickLink-Wanted-List.

## Modelle

| Modell | Teile | Beschreibung |
|---|---|---|
| [MBDTF-Relief](mbdtf-relief/) | 40.417 | Kanye Wests *My Beautiful Dark Twisted Fantasy* als 128×128-3D-Relief: rotes Stofffeld, erhabener Goldrahmen, vertiefte Leinwand, Ballerina mit echtem Weinglas |
| [MBDTF-Diorama](mbdtf-diorama/) | 7.813 | Szenen-Set „Runaway“ (48×48): Cover als 3D-Reliefwand per SNOT, 33 Minifiguren – Kanye am Flügel, 21 Ballerinen, Dinnertafel, Phoenix |
| [UTOPIA-Relief](utopia-relief/) | 10.993 | Travis Scotts *UTOPIA* als 96×96-3D-Relief: modellierte Figur (Muskeln, Glanzlichter, Silberhose) tritt bis 17 Platten aus dem schwarzen Grund; 64×64-Variante |
| [ASTROWORLD-Relief](astroworld-relief/) | 25.099 | Travis Scotts *ASTROWORLD* als 96×96-3D-Relief: goldener Kopf als Kuppel (Pearl Gold), vertiefter Eingang, Kinder und Rakete als Ebenen |
| [Graduation-Relief](graduation-relief/) | 28.210 | Kanye Wests Albumcover *Graduation* als 96×96-3D-Relief (ca. 77 × 77 cm, bis 5 cm tief, Satellitenschüsseln am Ring) im Stil von LEGO-Wandkunst – jede Noppe ein anderes Teil in anderer Höhe |
| [Circus Maximus (UTOPIA)](circus-maximus/) | 7.434 | Travis Scotts Arena-Bühne nach dem Bühnenentwurf auf 2 Baseplates 48×48: flacher Felspfad mit Felsgraten und Felstreppen, 12 runde Steinköpfe mit gemeißelten Gesichtern, Reliefgesichter, Felsspitzen, Glut und Geröll, Felsblock mit Durchgang und Travis, 16 Flammen, hoher Feuer-Videoring mit Lampenreihe, 169 Fans; Konzert-Render mit Dunst |
| [Yeezus Stage](yeezus-stage/) | 2.329 | Mount Yeezus: Fels-Pyramide mit Wendelweg bis zum Gipfel, darüber der Screen als Ellipse, Laufsteg mit Rampe zur ansteigenden Center Stage (Keil), Line-Arrays und Moving Heads an schwarzer Traverse, optionale Figuren (Kanye, Tänzerinnen, Jesus) – auf 2 Baseplates |
| [Mos Eisley Cantina](cantina/) | 1.375 | Hub aus *LEGO Star Wars: The Complete Saga*: runder Adobe-Raum mit 6 Episoden-Türen (SNOT-Leuchten, Rolladen), Bar mit Barkeeper, runde Tische, Bacta-Tanks, Kamin, Studs und Goldsteine – auf 2 Baseplates |
| [Saint Pablo Tour](saint-pablo/) | 3.105 | Kanye Wests schwebende Bühne von 2016: Plattform mit Gitterträgern und Randleuchten an 4 Seilen (J-Bogen, Länge aus der Schnur 63142) unter einem Lichtraster mit 582 hängenden Leuchten, Kanye mit Mikrofon, 133 Fans im Moshpit; Konzert-Render mit Dunst – auf einer Baseplate 48×48 |
| [Globe Stage](globe-stage/) | 10.876 | Stadion-Konzertbühne mit gerundeter Erdkugel-Kuppel, echter LED-Beleuchtung (Ring + 24 Scheinwerfer), einem Truss-Ring an Seilen unter einem Dach auf vier schlanken Ecktürmen und dem Album-Cover als Dach-Mosaik |

![Globe Stage](globe-stage/renders/globe_stage_hero.png)

Bauanleitung als PDF: [`globe-stage/Bauanleitung_Globe_Stage.pdf`](globe-stage/Bauanleitung_Globe_Stage.pdf)

![Yeezus Stage](yeezus-stage/renders/yeezus_hero.png)

## Skill: LEGO-Profi-Designer

[`.claude/skills/lego-profi-designer`](.claude/skills/lego-profi-designer/SKILL.md) bündelt Bautechniken,
Design-Prinzipien, Statik/legale Verbindungen, eine geprüfte Teile-Bibliothek und die Generator-Pipeline
dieses Repos. Claude Code lädt ihn automatisch, wenn in diesem Repo an LEGO-Modellen gearbeitet wird.

**Weitermachen (lokal):** siehe [`WEITERMACHEN.md`](WEITERMACHEN.md).

## Werkzeuge

- [`tools/relief`](tools/relief/) – Relief-Mosaik im Stil von LEGO-Wandkunst (mbrick_art): Bild → 3D-Pixel aus gemischten Teilen mit Tiefe und Konfetti-Farben.
- [`tools/mosaic`](tools/mosaic/make_mosaic.py) – Mosaik-Generator für 1 × 1-Fliesen: erzeugt mehrere Varianten und bewertet sie gegen die Vorlage (ΔL\* aus Abstand, SSIM im Detail).
- [`tools/ldraw-render`](tools/ldraw-render/) – Headless-Renderer für LDraw/MPD (three.js + Chromium) und
  `ldbbox.py` zum Nachschlagen von Teil-Abmessungen und Ursprüngen.
