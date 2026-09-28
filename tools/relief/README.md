# Relief-Mosaik („Chaos-Pixel-Art")

Macht aus einem Bild ein LEGO-Wandbild im Stil von [mbrick_art](https://www.tiktok.com/@mbrick_art/video/7288804014462897440):
1 Noppe = 1 Pixel, aber jede Zelle hat ein anderes Abschlussteil (Rundstein, Kegel, Rundplatte, Fliese, Technic-Stein,
Gitter, Cheese-Slope, Blüte …) und eine andere Höhe. Aus der Entfernung erkennt man das Motiv, aus der Nähe eine lebendige
Textur mit bunten Konfetti-Farben.

```bash
python3 tools/relief/make_relief.py bild.jpg ausgabe/name --breite 48 --hoehe 48 --chaos 0.35 --konfetti 0.05 --tiefe 3
```

| Option | Wirkung |
|---|---|
| `--breite`, `--hoehe` | Größe in Noppen (Grundplatten 48 × 48 werden automatisch gesetzt) |
| `--chaos` | Anteil Zellen mit der zweitnächsten Farbe – Farbmischung statt glatter Flächen |
| `--konfetti` | Anteil bunter Akzentfarben mit gleicher Helligkeit (Lila, Lime, Pink, Azur …) |
| `--tiefe` | zufällige Zusatz-Platten pro Zelle (Grundrauschen) |
| `--wolken` | Hintergrund-Relief: helle Bildstellen bis zu N Platten höher |
| `--licht` | Licht und Schatten wie ein Maler (Licht von links oben, Farbstufen gleichen Farbtons, gedithert); `0` = aus |
| `--formfolge` | Slopes zeigen mit dem Gefälle der Höhenkarte (runde Formen) |
| `--farben-plus` | Zusatzfarben: 3 Dark Turquoise, 151 Sand Green, 92 Nougat, 78 Light Nougat, 297 Pearl Gold, 47/36 Trans |
| `--zonen` | JSON-Datei: Bildteile mit eigener Höhe (flach/Kuppel), Teile-Pools, Farbe und Spezialteilen (Schüsseln, Blumen, Weinglas …), Pinselstrichen (`striche`), Konturen (`kontur`), Farbmix (`mischung`), handgesetzten Einzelteilen (`teil`), `sauber`, `glatt`, `licht`, Beispiel [`graduation-relief/zonen.json`](../../graduation-relief/zonen.json) |
| `--farben` | eingeschränkte Palette als LDraw-Codes, z. B. `0,15,71,72,4,25` |
| `--seed` | andere Zufallsverteilung der Teile |

Ausgabe: `name.mpd`, `name_bom.csv`, `name_bricklink.xml`, `name_vorschau.png` (flache Farbvorschau).

## Demo

Aus einem Render der Circus-Maximus-Bühne (48 × 48 Noppen, 6.212 Teile):

| Frontal (wie an der Wand) | Nah: Tiefe und Konfetti |
|---|---|
| ![Front](demo/relief_front.png) | ![Nah](demo/relief_nah.png) |

![Schräg](demo/relief_schraeg.png)
