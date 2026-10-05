# Weitermachen – Übergabe

Stand aller LEGO-Projekte aus der Claude-Code-Session, damit du lokal (Claude Desktop oder `claude` im Terminal)
nahtlos weiterarbeiten kannst. Öffne diesen Ordner in Claude Code und sag z. B.: *„Lies WEITERMACHEN.md und mach
mit der Circus-Maximus-Bühne weiter."*

## Git

- Repo: `herbs44/lego-`, Branch **`claude/new-github-repo-3mlbqx`** (alles gepusht, kein PR).
- Lokal holen: `git clone https://github.com/herbs44/lego-.git && cd lego- && git checkout claude/new-github-repo-3mlbqx`
- Oder dieses ZIP entpacken (enthält den gleichen Stand ohne Git-Historie).

## Projekte

| Ordner | Stand | Generator | Teile |
|---|---|---|---|
| `globe-stage/` | fertig inkl. PDF-Bauanleitung, Bully-Mosaik auf dem Dach | `generate_globe_stage.py` | 10.876 |
| `yeezus-stage/` | Mount Yeezus mit Wendelweg, rein unbunt; Stud.io-Bauanleitung (`yeezus_stage_anleitung.mpd`) und 360°-Video | `generate_yeezus_stage.py` | 2.301 |
| `circus-maximus/` | Travis Scott UTOPIA, 2×48×48, überarbeitet nach Recherche (Entwurf Elsa Hanneke): runde Steinköpfe mit gemeißelten Gesichtern (Headlight-Augen), Reliefgesichter, Felsgrate mit Treppen, Spitzen, Glut, Geröll, hoher Feuer-Ring mit Lampen, Fans mit Hauttönen; Konzertlicht `render_konzert.py` | `generate_circus_maximus.py` | 7.434 |
| `circus-maximus-metlife/` | MetLife 09.10.2024, 128×64, V1 aus Textquellen (Fotos gesperrt) – README mit 21 Abschnitten, Blueprint, Ansichten | `generate_metlife_stage.py` + `blueprint.py` | 13.613 |
| `mbdtf-relief/` | *MBDTF* als 128×128-3D-Relief wie gemalt (Pinselstriche, Licht/Schatten, Goldrahmen, Weinglas) | `tools/relief/make_relief.py` + `zonen.json`, Optionen `--licht 1 --formfolge` | 40.417 |
| `mbdtf-diorama/` | MBDTF-Szene „Runaway“: Reliefwand (48×48, SNOT), Kanye am Flügel, 21 Ballerinen, Dinnertafel, Phoenix | `generate_mbdtf_diorama.py` + `wand_relief.mpd` | 7.813 |
| `utopia-relief/` | Travis Scott *UTOPIA* als 96×96-Relief (+ 64×64), Höhe nach Helligkeit | `vorbereiten.py` + `make_relief.py --hell-hoehe 16` (Aufruf im README) | 10.993 |
| `astroworld-relief/` | Travis Scott *ASTROWORLD* als 96×96-Relief, Gesicht als Gold-Kuppel | `make_relief.py` + `zonen.json` (Zonen-Schlüssel `palette`) | 25.099 |
| `cantina/` | Mos Eisley Cantina (Hub aus LEGO Star Wars: The Complete Saga), 6 Episoden-Türen, Bar, Tische, Bacta-Tanks, optionale Figuren | `generate_cantina.py` | 1.375 |
| `saint-pablo/` | Saint Pablo Tour: schwebende Plattform an 4 Seilen (63142 im J-Bogen in den Endblöcken der Gitterträger 30518), Lichtraster mit 582 Leuchten auf 6 Gittertürmen, Kanye + 133 Fans; Konzertlicht-Render `render_konzert.py` | `generate_saint_pablo.py` | 3.105 |
| `graduation-relief/` | Kanye *Graduation* als 96×96-3D-Relief mit Satellitenschüsseln | `tools/relief/make_relief.py` + `zonen.json` | 28.210 |

Jeder Generator schreibt `.mpd`, Stückliste `_bom.csv` und `_bricklink.xml` und prüft sich selbst
(0 lose, 0 schwebende Teile, 0 Kollisionen). Neu erzeugen: `python3 <ordner>/generate_….py`.

Graduation neu erzeugen (Cover-Bild liegt aus Urheberrechtsgründen nicht im Repo):
```bash
python3 tools/relief/make_relief.py cover.jpg graduation-relief/graduation_relief --breite 96 --hoehe 96 \
  --chaos 0.22 --konfetti 0.035 --seed 3 --tiefe 2 --wolken 4 --zonen graduation-relief/zonen.json
```

## Werkzeuge

- `tools/ldraw-render/` – Renderer (three.js + Playwright/Chromium): `npm install`, dann
  `MODEL_DIR=<ordner> node server.js &` und `node shoot.js modell.mpd out/name '{"hero":[55,22,0.95]}'`.
  Lokal ist oft Stud.io einfacher: `.mpd` direkt öffnen.
- `tools/relief/make_relief.py` – Bild → Relief-Mosaik (Zonen, Spezialteile, Höhenkarte, `.ldr` für BrickLink).
- `tools/mosaic/make_mosaic.py` – flache 1×1-Fliesen-Mosaike mit Bewertung.
- `tools/ldraw-render/ldbbox.py <teil>` – Ursprung und Maße eines Teils nachschlagen.
- `tools/blender-render/render_cycles.py` – fotorealistische Standbilder in Blender (Cycles, GPU, lokale LDraw-Bibliothek):
  `blender -b -P tools/blender-render/render_cycles.py -- modell.mpd out/name [--views '{"hero":[-55,24,1]}']`.
  LDraw-Import, Farben und Aufbau-Animation liegen in `tools/blender-render/ldraw_blender.py`
  (Bibliothek: `$LDRAWDIR`, sonst die von Stud.io).
- `yeezus-stage/anleitung/plan_steps.py` – Bauschritte planen und prüfen, schreibt `yeezus_stage_anleitung.mpd`
  mit `0 STEP` für den Stud.io Instruction Maker (Traverse, Moving Head, Line-Array als Baugruppen) und
  `schritte.txt` mit Titeln und Hinweisen je Schritt.

## Videos (Blender/EEVEE, Musik nicht im Repo)

- `mbdtf-relief/video/runaway_video.py` – 20-s-Clip zu *Runaway*: Relief baut sich auf den Klaviertönen auf,
  Drop, 2 Takte, Schnitt auf Schwarz. `blender -b -P mbdtf-relief/video/runaway_video.py -- "<runaway.mp3>" out/runaway20`
- `yeezus-stage/video/coldest_winter_video.py` – 360°-Diorama zu *Coldest Winter*, Zeitraffer-Aufbau auf einen
  Lego-Bau-Sound, Lichtkegel im Dunst. `blender -b -P yeezus-stage/video/coldest_winter_video.py -- "<Coldest Winter.mp3>" "<lego-build.mp3>" out/coldest_winter`
- `circus-maximus/video/hyaena_video.py` – Bühnen-Präsentation zu *HYAENA* im orangen Konzertlicht: Fahrten über die
  Bühne, in der Pause vor dem Drop POV aus dem dunklen Lift-Schacht, auf dem Drop wird Travis aus dem Lift nach oben
  geschleudert (POV), landet mit Drehung; danach Schnitte auf dem Beat-Raster, Flammen/Ring pulsieren.
  Drop, Pause und Tempo werden erkannt (HYAENA: Drop 27,39 s, Pause 20,0–24,2 s, 96,6 BPM).
  `blender -b -P circus-maximus/video/hyaena_video.py -- "<HYAENA.mp3>" out/hyaena` (ca. 3 s/Bild in 1080p).
- Alle mit `--probe` (Standbilder zum Prüfen) und `--blend` (Szene mit Kamera-Markern).
  Timing wird aus der Musik gelesen; Ausgabe landet in `out/` (nicht im Repo).

## Skill

`.claude/skills/lego-profi-designer/` – wird von Claude Code in diesem Ordner automatisch geladen: Arbeitsablauf,
Geometrie/SNOT, Technik-Katalog (inkl. Relief-Mosaik), Design, Statik, geprüfte Teile, Pipeline-Stolperfallen.

## Deine Vorlieben (bitte beibehalten)

- Kommunikation auf Deutsch; iterativ arbeiten und jede Änderung rendern und prüfen.
- Globe: keine Minifiguren. Yeezus: Figuren als abnehmbare Baugruppe `11_figuren` (Kanye, 12 Tänzerinnen, Jesus), rein unbunt.
- Rundungen mit kurzen Slopes (1×1/2×1), keine langen.
- Yeezus: Türme, Gitterträger und Traverse schwarz; Center Stage als ansteigender Keil; Screen als Ellipse über dem Gipfel.
- Yeezus: rein unbunt, **kein Rot**.
- Circus Maximus: keine fliegenden Köpfe; Weg niedrig (3 Steine); Stage dunkel; Fans **komplett schwarz**;
  wenige Flammen, mehr Dynamik.
- Relief-Kunst: viel Z-Tiefe, viele verschiedene Teile, Teile mit Bedeutung (z. B. Schüsseln am Ring).
- Keine Referenzfotos ins Repo committen.

## BrickLink

- Upload nur als **XML** (Reiter „Upload BrickLink XML format") – `.mpd` wird nicht akzeptiert, `.ldr` macht Fehler.
- Getestet: 3062b/3068b/3069b/3070b werden abgelehnt → im XML **3062/3068/3069/3070** (schon so in allen Dateien).
- 2412b und 3794b wurden akzeptiert. Ungetestet: 3040b, 4460b (Bühnen) – bei Fehlern Nummer ohne „b" probieren.

## Offene Ideen

- Graduation: lesbarer Titel als eigener Fliesen-Schriftzug oder größere Version mit hochaufgelöstem Cover.
- Circus Maximus: Handy-Lichter bei den Fans, Lift auf dem Block, optional der fliegende Riesenkopf (bisher auf Wunsch weggelassen).
- Yeezus: PDF-Bauanleitung wie bei der Globe Stage (Vorlage `globe-stage/anleitung/`).
- Flache `.ldr`-Exporte der Bühnen für Stud.io/BrickLink.
