# Generator-Pipeline, Renders und Stolperfallen

Vorlagen im Repo `herbs44/lego-`:
- `yeezus-stage/generate_yeezus_stage.py` – Höhenfeld-Landschaft (Fels, Wege, Überhänge), Screen-Mosaik,
  Traverse, SNOT-Anbauten, vollständige Checks. **Beste Vorlage für neue Modelle.**
- `globe-stage/generate_globe_stage.py` – Kuppel/Kugel, Truss-Ring, Seile, LEDs, Dach-Mosaik.
- `globe-stage/anleitung/plan_steps.py` + `make_pdf.py` – Bauschritte planen, prüfen und als PDF setzen.
- `tools/ldraw-render/` – Headless-Renderer; `tools/mosaic/make_mosaic.py` – Mosaik-Varianten mit Bewertung.

## Architektur

1. **Höhenfeld / Zellmengen**: `HF[(x,z)] = Höhe in Steinen`, `MAT[(x,z)] = Material` (podest, berg,
   weg, fels, laufsteg …). Formen aus Ebenen (`planes_height`), Kappungen, Rauschfunktionen, Rissen.
2. **Zwangsbedingungen**: z. B. Weg-Stationen mit Höhe in Platten; bergseitig `≥ Weg + 1`,
   talseitig `≤ Weg`; geometrische Klassifikation über die Talrichtung der Station (nicht über Höhen
   raten); danach Mulden füllen.
3. **Schale + Decks**: pro Lage `S[g] = {Zellen mit HF > g}`; Außenband massiv, Inneres Decks auf Pfeilern;
   Stütz-Propagation von oben nach unten.
4. **Slopes an Stufenkanten**: Teil nach Stufenbreite (1/2/3 Zellen → 45°/33°/18°) und Stufenhöhe
   (2/3 Steine → 65°/75°); Zellen als `replaced`/`covered` markieren; Wege nie überdecken.
5. **Packing**: gleichfarbige Rechtecke, größte zuerst; Vorzugsachse und Scanrichtung pro Lage
   wechseln (Verbund). Unsichtbares Inneres schwarz und groß.
6. **Kappen**: offene Oberseiten mit Curved/Cheese (Rauschen verteilt) oder Fliesen; Sonderflächen
   (Dielen, Wegstufen, Gipfel) eigene Routinen.
7. **Anbauten**: SNOT-Teile mit expliziter Verbindung (`SNOT_LINKS`), hängende Teile `hang=True`.
8. **Checks** (siehe `statik-und-legal.md`) → Export MPD (Submodelle), BOM-CSV, BrickLink-XML.

Datenstruktur je Teil: `Part(sub, name, color, x, y, z, rot, cells, ytop, ybot, studs, hang, extra,
studcells)` – `cells`/`ytop`/`ybot` sind die Grundlage für Graph- und Kollisionscheck.

## Renders

```bash
cd tools/ldraw-render && npm install
MODEL_DIR=<ordner mit mpd> node server.js &          # :8765, lädt Teile aus dem GitHub-Mirror, Cache
node shoot.js modell.mpd out/praefix '{"hero":[62,16,0.9],"front":[90,1,0.62,-300,-330,0]}'
```

- View `[az, el, abstand, zielX, zielY, zielZ, fov]`: az 0 = Kamera bei +z, az 90 = Kamera bei −x,
  az 180 = Kamera bei −z, az −90 = Kamera bei +x. Ziel in LDraw-Koordinaten (y nach unten).
- Server in einer Neustart-Schleife laufen lassen (stürzt bei langen Sessions ab); bei EADDRINUSE alten
  Prozess beenden. Nach Container-Neustart neu starten.
- Standardansichten pro Projekt festlegen und immer gleich rendern (vorher/nachher vergleichbar).
- Jeden Render selbst ansehen; bei Detailfragen gezielte Nahansichten rendern.

## Stolperfallen (alle in diesem Repo passiert)

| Problem | Lösung |
|---|---|
| Achsen verwechselt: von vorne (Blick von −x) liegt +z **links** | Mosaike/Karten per Korrelation Render ↔ Vorlage prüfen |
| Seitenansicht für Frontansicht gehalten | Blickrichtung der Vorlage klären, Ausrichtung im README dokumentieren |
| `cos(180°)` liefert Rauschen → Ebenen kippen über die Rundung | `round(wert, 6)` vor dem Runden |
| Pythons `round()` rundet 12,5 auf 12 (Banker's Rounding) | `math.floor(x + 0.5)` |
| Weg-Nachbarn per Höhe als berg-/talseitig geraten → falsche Wände | Talrichtung der Station geometrisch nutzen |
| Rinne hinter Wegkante | Schulter 2–3 Zellen bergseitig + Muldenfüllung |
| Kollision mit Türmen/Reserviertem | reservierte Zellen aus Höhenfeld und Slope-Läufen ausnehmen |
| Untere Plattenlagen nicht verbunden | Verbund-Algorithmus (Kruskal-artig) und Check auf 1 Komponente |
| Teil-Ursprung falsch vermutet | `scripts/ldbbox.py` vor Einsatz |
| Doppelte Code-Anker beim Patchen | Patch-Skripte mit `assert s.count(alt) == 1` |
| WebFetch auf Fachseiten/YouTube blockiert | WebSearch nutzen oder Nutzer um Screenshots/Freigabe bitten |

## Lieferung

- Generator im Repo, Ausgabe: `<name>.mpd`, `<name>_bom.csv`, `<name>_bricklink.xml`, `renders/*.png`.
- README: Kennzahlen (Teile, Positionen, Maße), Ausrichtung, Renders, Aufbau (Submodelle),
  angewandte Techniken mit Umsetzung, Prüfergebnis, Hinweise (seltene Teile, Abweichungen zur Realität).
- Commit-Nachricht beschreibt Änderungen und Check-Ergebnis; keine Referenzfotos committen.
