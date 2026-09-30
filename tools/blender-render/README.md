# Blender-Render (Cycles) für LDraw-Modelle

Fotorealistische Bilder der Modelle mit echtem Kunststoff-Material, weichen Schatten und Tiefenunschärfe – ohne
Add-on. `render_blender.py` lädt die Teile-Geometrie aus der LDraw-Bibliothek (über den Server aus
[`tools/ldraw-render`](../ldraw-render/), der fehlende Dateien holt und cached), baut jedes Teil einmal als Mesh
(alle Kopien teilen sich die Daten), setzt Materialien nach LDConfig und rendert mit Cycles + Denoiser.

## Einrichten

```bash
python3.11 -m venv bvenv && ./bvenv/bin/pip install bpy==5.0.1      # Blender als Python-Modul
cd tools/ldraw-render && npm install && MODEL_DIR=. node server.js &   # Teile-Server (einmal starten)
```

Mit installiertem Blender geht es auch ohne venv: `blender -b -P render_blender.py -- modell.mpd …`.

## Aufruf

```bash
./bvenv/bin/python tools/blender-render/render_blender.py mbdtf-relief/mbdtf_relief.mpd mbdtf-relief/blender/mbdtf \
  --views mbdtf-relief/blender_views.json --samples 96 --breite 1600 --hoehe 1600
```

| Option | Wirkung |
|---|---|
| `--ansicht wand` | Wandbild: Noppen zum Betrachter (+Y), Bild oben = +Z, weiße Galeriewand, Licht von links oben (Standard) |
| `--ansicht oben` | Modell wie gebaut (Bühnen), Studio-Licht |
| `--views` | JSON mit Kameras: `{"name": {"cam": [x,y,z], "ziel": [x,y,z], "brennweite": 50, "blende": 2.8}}` (Meter; `blende` = Tiefenunschärfe) |
| `--samples`, `--breite`, `--hoehe` | Qualität und Auflösung |
| `--belichtung` | Belichtungskorrektur in Blendenstufen (Standard −0,3) |
| `--wand` | Wandfarbe als sRGB, z. B. `0.2,0.2,0.22` für eine dunkle Wand |

Materialien: ABS mit leichtem Klarlack (Rauheit 0,22), Trans-Farben als Glas (Transmission), Pearl/Metallic-Farben
metallisch. Farbmanagement „Khronos PBR Neutral" für farbtreue LEGO-Farben. Maßstab: 1 LDU = 0,4 mm.

Dauer (4 CPU-Kerne): Laden von ca. 22.000 Teilen ~20 s, ein Bild 1600 × 1600 mit 96 Samples einige Minuten.

## Lokal ohne Server: `ldraw_blender.py`, `render_cycles.py` und die Videos

Für lokales Arbeiten mit installiertem Blender (Windows, GPU) gibt es eine zweite Variante, die die LDraw-Bibliothek
direkt von der Platte liest (`$LDRAWDIR`, sonst die von Stud.io, sonst der Cache von `tools/ldraw-render`):

- `ldraw_blender.py` – gemeinsamer Import: BFC-Windungsrichtung, LDConfig-Farben, je Farbe ein Objekt, Teil-Attribute
  (z. B. Einbauzeit), Aufbau-Animation per Geometry Nodes (`add_build_anim`), Alpha-Glas für EEVEE, GPU-Auswahl.
- `render_cycles.py` – Standbilder mit Cycles auf der GPU; Reliefs und Bühnen werden automatisch gerahmt:
  `blender -b -P tools/blender-render/render_cycles.py -- modell.mpd out/name [--views '{"hero":[-55,24,1]}'] [--res 1600x1200]`
- Videos (EEVEE, Timing aus der Musik, Musik bleibt lokal): `mbdtf-relief/video/runaway_video.py`,
  `yeezus-stage/video/coldest_winter_video.py` – jeweils mit `--probe` für Standbilder und `--blend` zum Nachbearbeiten.
