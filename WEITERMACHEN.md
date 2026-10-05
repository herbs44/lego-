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
| `yeezus-stage/` | Mount Yeezus mit Wendelweg, rein unbunt | `generate_yeezus_stage.py` | 2.301 |
| `circus-maximus/` | Travis Scott UTOPIA, 2×48×48, schwarze Fans, Pyro/CO2 | `generate_circus_maximus.py` | 7.062 |
| `circus-maximus-metlife/` | MetLife 09.10.2024, 128×64, V1 aus Textquellen (Fotos gesperrt) – README mit 21 Abschnitten, Blueprint, Ansichten | `generate_metlife_stage.py` + `blueprint.py` | 13.613 |
| `mbdtf-relief/` | *MBDTF* als 128×128-3D-Relief wie gemalt (Pinselstriche, Licht/Schatten, Goldrahmen, Weinglas) | `tools/relief/make_relief.py` + `zonen.json`, Optionen `--licht 1 --formfolge` | 40.417 |
| `mbdtf-diorama/` | MBDTF-Szene „Runaway“: Reliefwand (48×48, SNOT), Kanye am Flügel, 21 Ballerinen, Dinnertafel, Phoenix | `generate_mbdtf_diorama.py` + `wand_relief.mpd` | 7.813 |
| `utopia-relief/` | Travis Scott *UTOPIA* als 96×96-Relief (+ 64×64), Höhe nach Helligkeit | `vorbereiten.py` + `make_relief.py --hell-hoehe 16` (Aufruf im README) | 10.993 |
| `astroworld-relief/` | Travis Scott *ASTROWORLD* als 96×96-Relief, Gesicht als Gold-Kuppel | `make_relief.py` + `zonen.json` (Zonen-Schlüssel `palette`) | 25.099 |
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

## Skill

`.claude/skills/lego-profi-designer/` – wird von Claude Code in diesem Ordner automatisch geladen: Arbeitsablauf,
Geometrie/SNOT, Technik-Katalog (inkl. Relief-Mosaik), Design, Statik, geprüfte Teile, Pipeline-Stolperfallen.

## Deine Vorlieben (bitte beibehalten)

- Kommunikation auf Deutsch; iterativ arbeiten und jede Änderung rendern und prüfen.
- Globe/Yeezus: keine Minifiguren; Rundungen mit kurzen Slopes (1×1/2×1), keine langen.
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
- Circus Maximus: Moshpit, Handy-Lichter bei den Fans, sichtbare Lichtstrahlen, Lift auf dem Block, Moai-Köpfe.
- Yeezus: PDF-Bauanleitung wie bei der Globe Stage (Vorlage `globe-stage/anleitung/`).
- Flache `.ldr`-Exporte der Bühnen für Stud.io/BrickLink.
