# ldraw-render

Headless-Renderer für LDraw/MPD-Modelle. Teile werden bei Bedarf aus der LDraw-Bibliothek
(GitHub-Mirror `gkjohnson/ldraw-parts-library`) geladen und in `cache/` abgelegt.

```bash
npm install                                   # three.js
MODEL_DIR=../../globe-stage node server.js &  # lokaler Server auf :8765
python3 prefetch.py ../../globe-stage/globe_stage.mpd   # optional: Teile vorab laden
node shoot.js globe_stage.mpd out/render '{"iso":[30,22,0.95],"top":[0,90,4,0,-400,0,8]}'
```

Views: `[azimut, elevation, abstand, zielX, zielY, zielZ, fov]`. Azimut 0 blickt von LDraw +z (Front),
das Ziel wird in LDraw-Koordinaten angegeben (y zeigt nach unten).

`shoot.js` erwartet Playwright mit Chromium. Der Pfad ist auf die globale Installation
`/opt/node22/lib/node_modules/playwright` eingestellt; bei Bedarf anpassen.

`ldbbox.py <teil> ...` gibt Titel und Bounding-Box eines Teils aus – nützlich, um Ursprung und
Ausrichtung vor dem Platzieren zu prüfen.

## Schritt-Renderer (Bauanleitungen)

`steps.html` + `steps.js` laden ein MPD **einmal** und rendern dann viele Aufträge: Jedes direkte Untermodell
(z. B. `step_001.ldr`) wird pro Auftrag normal, blass oder unsichtbar geschaltet.

```bash
node steps.js anleitung.mpd jobs.json ausgabe/
```

Auftrag: `{"name", "show": [...], "fade": [...], "frame": [...], "az", "el", "w", "h", "radius"?, "target"?}` –
`frame` bestimmt den Bildausschnitt, `radius`/`target` (LDraw-Koordinaten) setzen ihn direkt.

