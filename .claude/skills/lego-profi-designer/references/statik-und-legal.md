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

LEGO veröffentlicht keine vollständige Liste der internen Regeln; bestätigt ist nur, dass es sie gibt und
dass Studio solche Verbindungen bei ausgeschaltetem Einrasten zulässt. Grenzwerte in dieser Datei sind
deshalb konservative Generator-Regeln, keine offiziellen LEGO-Werte.

**Clips**: Ein Clip darf beim Einsetzen kurz aufgehen, muss aber in seine Ausgangsform zurückkehren –
dauerhaft aufgeweitet ist Spannung. Neuere Clip-Formen machen manche alte Problemverbindung legal: die
konkrete Formvariante prüfen, nicht nur die Teilenummer. Stange + Clip: neutral = in Ordnung,
kontrolliert gebogen = Näherung, erzwungen gebogen = vermeiden.

**Spannungsklassen** für Verbindungen im Generator (ab 3 ist ein echter Test mit Steinen nötig):

| Klasse | Bedeutung |
|---|---|
| 0 | keine relevante Spannung |
| 1 | normale Kupplung (Noppe, Pin, Scharnier) |
| 2 | Reibsitz (Stange in Clip/Hohlnoppe, Drehteller) |
| 3 | elastisches Element beteiligt (Clip unter Last, Beinahe-Tripel am Scharnier) |
| 4 | starke Dauerverformung |
| 5 | vermeiden |

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

Konservative Grenzwerte (Heuristik für Display-Modelle, nicht von LEGO):
- **Senkrechte Fugen** nicht über mehr als 2 Steinhöhen ungekreuzt durchlaufen lassen.
- **Schale**: Außenhaut 1–2 Studs, Rippen/Pfeiler im Abstand 8–12 Studs (kleine Modelle) bzw. 6–8 Studs
  (große, schwere Modelle), dazwischen hohl.
- **Auskragung gesamt**: nur Platten bis 4 Studs, massiv aus Steinen bis 6 Studs, Truss bis 8 Studs ohne
  zweite Lastlinie. Überhang bis 2 Studs normal, 3–4 Studs mit Gegenanker, darüber Kern/Technic/Truss.
- **Hängendes** (Screens, Arrays, Truss): 1 Aufhängepunkt nicht akzeptieren, 2 mittel, ab 3 gut. Eine
  sichtbare Deko-Verbindung darf nie der einzige Lastpfad sein.
- **Große Basen**: nicht nur große Platten aneinander – untere Plattenlage, Steinkern, obere Plattenlage,
  Fugen nicht auf einer Achse (2x6/2x8-Platten 3795/3034, Technic-Platten 3709b).
- **Transport**: Module höchstens 32×32 Studs (bei schweren Bühnen 16×16 bis 32×32), an den Rändern mit
  Technic-Pins (2780) verbinden und erst vor Ort zusammensetzen.

## Automatische Prüfung (Generator)

- **Verbindungsgraph**: Kante, wenn Unterkante eines Teils auf Noppenzellen eines anderen trifft
  (gleiche y-Ebene, Zellüberlappung). Zusätzlich explizite Seitenverbindungen (SNOT, Schlingen).
  Alles muss von den Baseplates aus erreichbar sein → `disconnected = 0`.
- **Schwebend**: Teil ohne Noppen darunter und nicht als hängend markiert → `floating = 0`.
- **Kollisionen**: Belegung pro Zelle in 2-LDU-Scheiben → `collisions = 0`.
- **Info**: Zellen ohne direkte Auflage zählen (kein Fehler, aber Hinweis auf Hebel).
- Hängende Teile nur mit `hang=True`, wenn sie oben mit Clutch hängen; Anzahl im README nennen.
