# Teile-Bibliothek (LDraw-IDs geprüft)

Alle IDs wurden in der LDraw-Bibliothek nachgeschlagen (`scripts/ldbbox.py`). BrickLink-IDs weichen
oft im Suffix ab: sicher bekannte Abweichungen stehen in der Spalte BL, sonst gilt die LDraw-ID –
beim ersten Import einer Wanted List fehlgeschlagene Positionen auf BrickLink nachschlagen und hier
ergänzen.

## Basis

| LDraw | BL | Name | Einsatz |
|---|---|---|---|
| 3811 | | Baseplate 32x32 | Grundfläche |
| 4186 | | Baseplate 48x48 | große Grundfläche |
| 3005 / 3004 / 3622 / 3010 / 3009 / 3008 / 6111 / 6112 / 2465 | | Brick 1x1 … 1x16 | Wände, Kern |
| 3003 / 3002 / 3001 / 2456 / 3007 / 3006 | | Brick 2x2 … 2x10 | Kern, Pfeiler |
| 3024 / 3023 / 3623 / 3710 / 3666 / 3460 / 4477 / 60479 | | Plate 1x1 … 1x12 | Lagen, Verbund |
| 3022 / 3021 / 3020 / 3795 / 3034 / 3832 / 2445 / 4282 | | Plate 2x2 … 2x16 | Decks |
| 3031 / 3032 / 3035 / 3030 / 3029 / 3958 / 3036 / 3033 / 3028 / 3456 / 3027 / 41539 / 92438 / 91405 | | große Platten bis 16x16 | Decks, Dächer |
| 3070b / 3069b / 63864 / 2431 / 6636 / 4162 | 3070 / 3069 / – | Tile 1x1 … 1x8 | Abdeckung, Dielen |
| 3068b / 87079 | 3068 / – | Tile 2x2 / 2x4 | glatte Flächen |

## Slopes und Kurven

| LDraw | Name | Einsatz |
|---|---|---|
| 60477 | Slope 18° 4x1 | Rampen, flache Böschung |
| 4286 / 3298 | Slope 33° 3x1 / 3x2 | Stufen 2 Studs breit |
| 3040b / 3039 | Slope 45° 2x1 / 2x2 | Standard-Stufe (BL-ID für 3040b prüfen) |
| 60481 | Slope 65° 2x1x2 | steile Wände, Grate |
| 4460b | Slope 75° 2x1x3 | Klippen |
| 30363 | Slope 18° 4x2 | breite Rampen |
| 3665a / 3660a | Slope 45° invertiert 2x1 / 2x2 | Überhänge (BL: 3665 / 3660) |
| 54200 / 85984 | Cheese 1x1 / 1x2 (Ursprung unten) | Kanten, Erosion, Paneele |
| 22388 | Slope 1x1 vierfach | Spitzen, Kappen |
| 11477 / 15068 | Curved 2x1 / 2x2 (Ursprung unten) | weiche Kanten, Rundungen |
| 93273 | Curved 4x1 doppelt | Firste, Wülste |
| 61678 / 50950 | Curved 4x1 / 3x1 | lange Kurven (Nutzer mag keine langen Slopes an Rundungen) |
| 6091 | Brick 2x1x1⅓ mit Rundung | Bögen, Kanten |
| 92946 | Slope-Platte 45° 2x1 | flache Schrägen, Kotflügel |

## Keile und Kurvenplatten

| LDraw | Name |
|---|---|
| 43722 / 43723 | Wedge 2x3 rechts/links |
| 41769 / 41770 | Wedge 2x4 rechts/links |
| 51739 | Wedge 2x4 (Spitze) |
| 2450 / 26601 | Platte 3x3 / 2x2 ohne Ecke |
| 2420 | Platte 2x2 Ecke |
| 25269 / 27925 / 27263 | Fliese 1x1 Viertelkreis / 2x2 Viertelkreis / 2x2 ohne Ecke |
| 30357 / 30565 / 80015 | Platte 3x3 und 4x4 mit Rundung, 5x5 Makkaroni |

## Rund

| LDraw | BL | Name |
|---|---|---|
| 6141 | 4073 | Plate 1x1 rund |
| 98138 | | Tile 1x1 rund |
| 14769 | | Tile 2x2 rund |
| 4032a | 4032 (prüfen) | Plate 2x2 rund |
| 3062b | 3062 | Brick 1x1 rund, Hohlnoppe |
| 3941 | | Brick 2x2 rund |
| 4589 / 3942c | | Kegel 1x1 / 2x2x2 |
| 3960 | | Schüssel 4x4 |
| 15470 | | Plate 1x1 rund mit Wirbel |
| 35480 | | Plate 1x2 mit runden Enden |

## SNOT und Versatz

| LDraw | Name | Hinweis |
|---|---|---|
| 87087 | Brick 1x1 Stud an 1 Seite | Referenz-Versatz 0 |
| 11211 | Brick 1x2 2 Studs an 1 Seite | Gitterfliesen, Fassaden |
| 30414 | Brick 1x4 Studs an der Seite | lange Fronten |
| 32952 | Brick 1x1x1⅔ Studs an 1 Seite | 5 Platten hoch = 2 Studs |
| 4733 / 47905 | Brick 1x1 Studs an 4 / 2 Seiten | SNOT-Kerne |
| 4070 | Brick 1x1 Headlight | ½ Platte zurückgesetzt |
| 99780 / 99781 | Bracket 1x2-1x2 up / down | |
| 99207 / 44728 | Bracket 1x2-2x2 up / down | |
| 2436b | Bracket 1x2-1x4 | |
| 3794b / 15573 | Jumper 1x2 | ½ Stud |
| 87580 | Jumper 2x2 | ½ Stud in beiden Achsen |

## Scharniere, Clips, Stangen, Gelenke

| LDraw | Name |
|---|---|
| 2429c01 | Scharnierplatte 1x4 drehbar |
| 44301a / 44302a | Rastscharnier 1x2, 1 bzw. 2 Finger (BL: 44301 / 44302) |
| 3680 / 3679 | Drehteller 2x2 Basis / Oberteil |
| 4085c / 4085b | Plate 1x1 Clip vertikal dick / dünn |
| 61252 / 6019 | Plate 1x1 Clip horizontal |
| 63868 | Plate 1x2 Clip am Ende |
| 4081b | Plate 1x1 Licht-Clip |
| 15712 / 2555 | Tile 1x1 mit Clip |
| 60478 / 48336 / 26047 | Plate mit Griff am Ende / an der Seite / Rundplatte mit Griff |
| 87994 / 30374 | Stange 3L / 4L |
| 14417 / 14418 / 14419 | Kugelgelenk-Platten |
| 3700 / 2780 / 4274 | Technic-Stein 1x2, Pin mit Reibung, Halbpin |
| 18677 | Plate 1x2 mit Pinloch unten |

## Textur und Details

| LDraw | BL | Name | Einsatz |
|---|---|---|---|
| 2412b | | Gitterfliese 1x2 | Lautsprecher, Lüftung, Bodenleuchten |
| 2877 | | Brick 1x2 mit Grille | Riefen/Rillen (Rillenseite im Render prüfen) |
| 98283 / 15533 | | Brick 1x2 / 1x4 mit Ziegelprägung | Mauerwerk |
| 30136 | | Brick 1x2 Log | Holz |
| 49668 | | Plate 1x1 mit Zahn | Zacken, Greebles |
| 24246 | | Tile 1x1 mit Rundende | Details |
| 6231 | | Panel 1x1x1 Ecke | Ecken, Nischen |
| 32028 | | Plate 1x2 mit Türschiene | SNOT-Rahmen |
| 3176 | | Plate 3x2 mit Loch | Achs-/Stangendurchführung |

## Bögen, Struktur, Pflanzen

| LDraw | BL | Name |
|---|---|---|
| 3659 / 4490 / 3455 / 92950 | | Bogen 1x4 / 1x3 / 1x6 / 1x6 erhöht |
| 3307 / 6005 | | Bogen 1x6x2 / 1x3x2 gekrümmt |
| 95347 | | Stütze 2x2x10 Gitterträger (in DBG seltener) |
| 63142 | x127c30pb01 | Schnur mit Endnoppen |
| 2423 / 32607 / 33291 | | Blätter 4x3 / Rundplatte mit 3 Blättern / Rundplatte mit Laschen (Blüte) |

## Farben (LDraw → BrickLink)

| LDraw | Name | BL |
|---|---|---|
| 0 | Black | 11 |
| 15 | White | 1 |
| 71 | Light Bluish Gray | 86 |
| 72 | Dark Bluish Gray | 85 |
| 1 / 2 / 4 / 14 | Blue / Green / Red / Yellow | 7 / 6 / 5 / 3 |
| 19 / 28 | Tan / Dark Tan | 2 / 69 |
| 70 / 308 | Reddish Brown / Dark Brown | 88 / 120 |
| 272 / 288 / 320 | Dark Blue / Dark Green / Dark Red | 63 / 80 / 59 |
| 73 / 212 | Medium Blue / Bright Light Blue | 42 / 105 |
| 47 / 46 | Trans-Clear / Trans-Yellow | 12 / 19 |
| 148 / 179 | Pearl Dark Gray / Flat Silver | 77 / 95 |

BrickLink-Upload: nur `.ldr`, `.io`, `.lxf`, `.bsx` oder XML – **kein `.mpd`**. XML ist am zuverlässigsten.
**Getestet (XML-Upload 2026):** 3062b, 3068b, 3069b, 3070b werden als „existiert nicht" abgelehnt – im XML immer
**3062, 3068, 3069, 3070** schreiben (auch wenn die Katalogseiten mit „b" im Web auftauchen). Rundplatte 1×1 = 4073.

BrickLink-XML: keine XML-Deklaration, Struktur `<INVENTORY><ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>…</ITEMID>
<COLOR>…</COLOR><MINQTY>…</MINQTY></ITEM></INVENTORY>`.
