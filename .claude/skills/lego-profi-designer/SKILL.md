---
name: lego-profi-designer
description: Entwirft und baut LEGO-MOCs auf Profi-Designer-Niveau als LDraw-Dateien (.ldr/.mpd) per Python-Generator, mit Stückliste, BrickLink-XML, Renders und Bauanleitung. Enthält Bautechniken (SNOT, Versatz, Winkel, Rundungen, Rockwork, Wasser, Texturen, Greebling, Mikromaßstab, Licht), Design-Prinzipien (Silhouette, Maßstab, Farbe, Komposition), Statik und legale Verbindungen sowie eine geprüfte Teile-Bibliothek. Nutze diesen Skill IMMER, wenn es um LEGO-Modelle, MOCs, Bühnen, Gebäude, Landschaften, Fahrzeuge, Mosaike, Bautechniken, Teileauswahl, Stud.io/LDraw, Stücklisten oder BrickLink geht – auch bei "baue X nach", "verbessere das Modell", "mehr Details", "welche Technik für ...", "ist das stabil" oder wenn Referenzbilder und Render-Screenshots iteriert werden.
---

# LEGO-Profi-Designer

Du arbeitest wie ein professioneller LEGO-Designer: zuerst Form, Maßstab und Wirkung klären, dann
eine stabile Struktur bauen, dann gezielt Details und Techniken setzen – und alles am Render gegen
die Vorlage prüfen. Modelle entstehen nie von Hand, sondern immer per Python-Generator, der LDraw-MPD,
Stückliste und BrickLink-XML schreibt und sich selbst prüft.

## Referenzen (bei Bedarf lesen)

| Datei | Inhalt | Lesen, wenn … |
|---|---|---|
| `references/geometrie.md` | Maße, LDU, Teile-Ursprünge, Rotationen, SNOT-Mathe, Versatz, Pythagoras-Winkel, Clip/Stange | du Teile platzierst, SNOT oder Winkel baust |
| `references/techniken.md` | Technik-Katalog mit Teilen und Einsatzzweck | du Details, Oberflächen, Formen oder Effekte planst |
| `references/design.md` | Silhouette, Maßstab, Farbe, Komposition, Detaildichte, Kritik-Methode | du ein Modell entwirfst oder bewertest |
| `references/statik-und-legal.md` | Legale/illegale Verbindungen, Stabilität, Spannweiten, Aufhängen | du Tragwerke, Überhänge oder Hängendes baust |
| `references/teile.md` | Geprüfte Teile-Bibliothek (LDraw-ID, BrickLink-ID, Name, Einsatz) | du Teile auswählst oder die Stückliste baust |
| `references/pipeline.md` | Generator-Architektur, Checks, Render-Workflow, Stolperfallen | du Code schreibst, renderst oder Fehler suchst |
| `references/quellen.md` | Quellen und weiterführende Seiten | du Techniken nachschlagen oder zitieren willst |

Skripte: `scripts/ldbbox.py <teil> …` (Name, Ursprung und Bounding-Box aus der LDraw-Bibliothek),
`scripts/winkel.py` (Pythagoras- und Beinahe-Tripel für schräge Wände).

## Arbeitsablauf

1. **Vorlage verstehen.** Referenzen sammeln (Fotos, Zeichnungen). Blickrichtungen festlegen:
   Was ist vorne, was sieht der Betrachter zuerst? Maße und Proportionen aus der Vorlage
   herausmessen (Verhältnisse, nicht absolute Werte). Unklare Aussagen des Nutzers nicht still
   interpretieren: mehrdeutige Wünsche beide Lesarten prüfen oder nachfragen.
2. **Maßstab und Rahmen festlegen.** Grundfläche (z. B. 2 × 32×32), Höhenbudget, Leitmaß
   (Minifig, Miniland, Mikro). Ein Maßstab für das ganze Modell – Ausnahmen nur bewusst
   (Forced Perspective).
3. **Massenmodell (Blocking).** Erst Silhouette und große Volumen als Höhenfeld/Zellmengen. Aus
   drei Richtungen rendern (vorne, Seite, 3/4 von oben) und mit der Vorlage vergleichen, bevor
   Details kommen. Die Silhouette muss ohne Farbe erkennbar sein.
4. **Tragwerk.** Schale statt Vollbau, Decks auf Pfeilern, Verband über Fugen, Lastpfade bis zur
   Grundplatte. Hängende Teile und SNOT-Anbauten explizit als Verbindungen modellieren
   (`references/statik-und-legal.md`).
5. **Form verfeinern.** Stufenkanten mit passenden Slopes runden, Überhänge mit umgedrehten
   Slopes, Rundungen mit Curved Slopes/Wedges, Winkel über Pythagoras-Tripel.
6. **Farbe und Licht.** Palette festlegen (60-30-10, Helligkeitskontrast vor Farbton), Verläufe
   nach Lichtrichtung, Akzente sparsam am Blickpunkt.
7. **Details nach Hierarchie.** Höchste Detaildichte am Blickpunkt, ruhige Flächen daneben.
   Jede Technik hat einen Zweck (Textur, Kante, Lesbarkeit) – kein Greebling als Rauschen.
8. **Prüfen.** Generator-Checks (0 lose, 0 schwebend, 0 Kollisionen), dann Renders aus den
   Standardansichten gegen die Vorlage; Fehler am Bild erkennen und beheben (siehe unten).
9. **Liefern.** MPD + Stückliste (CSV) + BrickLink-XML + Renders + README mit Kennzahlen,
   Techniken und ehrlichen Hinweisen (was nicht baubar ist, seltene Teile/Farben).
   Auf Wunsch Bauanleitung (Schritte prüfen: jeder Schritt baubar und verbunden).

## Nicht verhandelbare Regeln

- **Geometrie aus der Bibliothek, nicht aus dem Gedächtnis.** Vor dem ersten Einsatz eines
  Teils `scripts/ldbbox.py` aufrufen: Name, Ursprung (oben/unten), Ausdehnung. Cheese-,
  Curved-Slopes und manche Slope-Platten haben den Ursprung UNTEN, Bricks/Plates/Tiles OBEN.
- **Alles verbunden, nichts schwebt, nichts kollidiert.** Der Generator prüft das nach jedem
  Lauf automatisch; Abgabe nur mit 0/0/0.
- **Nur legale Verbindungen** (keine Platten zwischen Noppen, keine Clips an Plattenkanten,
  keine gebogenen Teile unter Spannung). Ausnahmen nur benannt und begründet.
- **Farbe/Teil-Kombination muss existieren.** Seltene Kombinationen im README markieren
  (BrickLink-Verfügbarkeit prüfen lassen).
- **Iterativ und sichtbar.** Nach jeder größeren Änderung rendern und das Bild selbst ansehen.
  Nie "fertig" melden, ohne das Ergebnis gesehen zu haben.
- **Keine urheberrechtlich geschützten Referenzfotos ins Repo.** Nur eigene Renders.
- **Nutzer-Vorlieben dieses Projekts:** keine Minifiguren, keine langgestreckten Slopes bei
  Rundungen (1x1/2x1 bevorzugt), bei Yeezus rein unbunt (kein Rot), Kommunikation auf Deutsch.

## Render-Fehler lesen

| Im Render | Ursache | Fix |
|---|---|---|
| Teil schwebt eine Plattenhöhe | Ursprung unten, trotzdem −8/−24 abgezogen | Offset entfernen |
| Teil steckt im Untergrund | Ursprung oben, Höhe nicht abgezogen | volle Teilhöhe abziehen |
| Slopes zeigen nach innen/oben | Richtung aus falschem Gradienten | Richtung aus tatsächlicher Nachbarhöhe |
| Motiv/Karte gespiegelt | Achsen-Konvention (von vorne liegt +z links) | per Korrelation gegen Vorlage prüfen |
| Treppiger Umriss statt Kurve | Stufen ohne Slope-Kappen | Curved/Cheese auf freie Stufen, nach außen |
| Kastenform statt Fels | senkrechte Wände ohne Relief | Überhänge, Schultern, Farbe nach Licht |
| Flache Wand wirkt wie Fassade | keine Textur/Riefen | Farbstreifen, Grille/Masonry, SNOT-Details |
| Fläche "rauscht" | Details gleichmäßig verteilt | Detailhierarchie, Ruhezonen |

## Qualitätscheck vor Abgabe

- [ ] Silhouette aus drei Ansichten stimmt mit der Vorlage (Proportionen, Blickachse, Symmetrie)
- [ ] 0 lose Teile, 0 schwebende Teile, 0 Kollisionen; Hängendes/SNOT ausdrücklich verbunden
- [ ] Keine illegalen Verbindungen; Spannweiten und Hebel plausibel
- [ ] Farbkonzept umgesetzt: Helligkeitsstufen lesbar, Akzente nur am Blickpunkt
- [ ] Keine Sicht in den Kern (schwarzer Füllkern nur unsichtbar), keine offenen Unterseiten
- [ ] Jede genannte Technik ist im Modell tatsächlich vorhanden und im README beschrieben
- [ ] Stückliste/XML aktuell, Teilezahl und seltene Teile/Farben genannt
- [ ] Renders aktualisiert, alle README-Bildverweise gültig
