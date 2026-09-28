# Statik und legale Verbindungen

## Legal / illegal

LEGO-Designer arbeiten nach internen Regeln: Keine Verbindung darf Teile dauerhaft unter Spannung
setzen, verformen oder nur durch Reibung an Stellen halten, die nicht dafür gedacht sind. „Illegal"
heißt „nicht standardkonform" – für MOCs gilt: vermeiden, und wenn doch, bewusst und benannt.

Nicht verwenden:
- Platte oder Fliese zwischen Noppen klemmen (drückt Noppen auseinander).
- Clip an einer Plattenkante oder anderen Nicht-Stangen festklemmen.
- Stange zwischen Noppen klemmen.
- Noppe in ein Technic-Loch stecken bzw. Technic-Pins in System-Unterseiten zwängen.
- Wände oder Platten biegen, um Kreise oder Bögen zu erzwingen.
- Teile mit Achsen zusammenhalten, die dabei biegen (z. B. Steine über eine Achse verbinden).
- Teile, die nur durch Klemmung an der Außenseite eines anderen Teils halten.

Legal und bewährt:
- Noppe in Anti-Stud, Stange in Clip/Hohlnoppe, Pin in Loch, Scharniere, Drehteller, Kugelgelenke.
- Platte diagonal nur auf den End-Noppen (Pythagoras-Tripel).
- SNOT über Stud-Bricks, Headlights, Brackets.

## Stabilität

- **Verband**: Fugen nie über mehrere Lagen übereinander; Packachse pro Lage wechseln.
- **Schale statt Vollbau**: Außen 2 Studs massiv, innen Decks aus 3 Plattenlagen auf 2x2-Pfeilern
  (Raster 4 Studs); mittlere Plattenlage per Verbund-Algorithmus so legen, dass alles ein Stück ist.
- **Stütz-Propagation**: Jede Zelle einer Lage braucht Auflage darunter (von oben nach unten
  kaskadieren); Ausnahme nur für ausdrücklich hängende Teile.
- **Hohe schlanke Bauteile**: Kern (Technic-Rahmen oder SNOT-Kern), alle 6–10 Steine mit Platten an
  die Außenwände binden; Dreiecke/Diagonalen gegen Schwanken.
- **Überhänge**: max. 1 Stud pro Lage ohne Unterstützung; größere Auskragung über umgedrehte Slopes,
  Brackets oder durchlaufende Platten mit Gegengewicht.
- **Spannweiten**: Deck/Brücke über Platten im Verband (mind. 2 Lagen, Stöße versetzt); lange
  Einzelplatten hängen durch.
- **Aufhängen**: Hängende Teile müssen von oben mit Noppen-Clutch halten; Seile (63142) tragen nur Zug.
  Last pro Noppe klein halten, mehrere Hänger verteilen.
- **Türme/Stützen**: Gitterträger 95347 gestapelt, Verbindungsplatten dazwischen; bei langen
  Traversen mehrere Stützen, im Check Tragkette bis zur Grundplatte.

## Automatische Prüfung (Generator)

- **Verbindungsgraph**: Kante, wenn Unterkante eines Teils auf Noppenzellen eines anderen trifft
  (gleiche y-Ebene, Zellüberlappung). Zusätzlich explizite Seitenverbindungen (SNOT, Schlingen).
  Alles muss von den Baseplates aus erreichbar sein → `disconnected = 0`.
- **Schwebend**: Teil ohne Noppen darunter und nicht als hängend markiert → `floating = 0`.
- **Kollisionen**: Belegung pro Zelle in 2-LDU-Scheiben → `collisions = 0`.
- **Info**: Zellen ohne direkte Auflage zählen (kein Fehler, aber Hinweis auf Hebel).
- Hängende Teile nur mit `hang=True`, wenn sie oben mit Clutch hängen; Anzahl im README nennen.
