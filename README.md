# Einlagern: was ist eine Abfahrtsschätzung wert? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-einlagern-schaetzung-umstauen-demo.streamlit.app/)** -->

Zwölftes Stück der Konzepte-Reihe **„Umstauen: Untergrenze und Suche“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Bisher war die Reihenfolge der Abfahrt **bekannt**. Hier ist sie beim **Einlagern** nur **geschätzt**: Die Container kommen nacheinander an und müssen **sofort** auf einen Stapel; danach werden sie in der Reihenfolge der **wahren** Abfahrt abgerufen, und was über dem nächsten liegt, wird **umgelagert**. Die Demo misst, **wie viel der Lücke** zwischen dem **niedrigsten Stapel** (kein Wissen) und dem **vollen Wissen** die Schätzung schließt, **ab welchem Schätzfehler** sie nichts mehr nützt und **wie weit das volle Wissen von der Untergrenze** der besten Ablage entfernt ist.

Die Fall-Demos [Stapelplanung](https://sebastianhanisch-stapelplanung-demo.streamlit.app/) (Block mit laufenden Ankünften und Abholungen, Kipppunkt des Schätzfehlers) und [Hofstellplatz](https://sebastianhanisch-hofstellplatz-demo.streamlit.app/) (vorausschauende Regel meist nicht besser als die naive) behandeln dieselbe Frage am Fall; **ihre Zahlen stehen dort und werden hier nicht wiederholt**. Hier wird **vom Verfahren her** gemessen, mit der Untergrenze als Maßstab.

## Warum dieses Problem

Eine Abfahrtsschätzung zum Einlagern kostet Aufwand; die Frage ist, was sie bringt. Die Messung zeigt drei Dinge. **Erstens** trägt die Schätzung weit: Bei einem Schätzfehler von 20 % der Containerzahl (σ = 0,2) schließt sie 54 bis 63 % der Lücke zwischen „niedrigster Stapel“ und vollem Wissen, bei σ = 0,1 rund 75 bis 83 %, bei σ = 0,05 90 bis 96 %. **Zweitens** kippt sie: Bei σ = 2 ist nichts mehr zu holen (0 bis 8 %), bei σ = 3 ist die Schätzung in fünf von sechs Zellen **schlechter** als der niedrigste Stapel. **Drittens** ist fast die ganze Lücke **Nichtwissen**, nicht Platzmangel: Mit vollem Wissen liegt die einfache Regel nahe an der **Untergrenze der besten Ablage** (0,61 gegen 0,49 Umlagerungen bei 4 × 4 mit 10 Containern), der niedrigste Stapel dagegen rund 3,5 darüber.

## Modell

**Eigene Umsetzung** an Zufallsbuchten; Einlagern unter unsicherer Abfahrt ist ein eigener Strang der Container-Stapelung („Stacking under uncertainty“, TU Delft; datengetriebene Online-Strategien, FSMJ 2022), aus Suchtreffern bekannt und **nicht gelesen**.

- **Bucht:** *S* Stapel der Höchsthöhe *H*, *N* Container (Füllgrad in Prozent der Plätze; es bleibt mindestens eine Stapelhöhe frei, so findet beim Abruf jeder Blocker einen Stapel mit Platz). Die Container kommen in zufälliger Reihenfolge an; jeder hat eine **wahre Abfahrtsnummer** 1 bis *N* (1 fährt zuerst ab).
- **Einlegen:** jeder Container wird beim Eintreffen sofort auf einen Stapel mit Platz gesetzt. **Zufälliger Stapel**; **niedrigster Stapel** (die wenigsten Container, keine Schätzung nötig); **engste Passung nach Schätzung** (Stück 1 auf geschätzten Nummern: der Stapel mit dem kleinsten frühesten Schätzwert, der später liegt als der des neuen Containers, sonst der mit dem größten frühesten Wert; leerer Stapel zuletzt).
- **Schätzung:** wahre Nummer + σ · *N* · *z* mit einer standardnormalen Zufallszahl *z* je Container (je Bucht fest, aus `random.Random(seed)`). σ = 0 ist **volles Wissen**.
- **Abruf:** in der Reihenfolge der wahren Abfahrt; liegt der nächste nicht oben, werden die Container darüber umgelagert (restricted, Regel „engste Passung“ nach den **wahren** Nummern). **Kosten = Zahl der Umlagerungen.**
- **Untergrenze der besten Ablage:** die kleinste Blockerzahl der fertigen Bucht über **alle** möglichen Platzierungen (Aufzählung der Zustände, bis 10 Container live). Jede Umlagerung bewegt einen Blocker, also gilt für **jede** Einlege-Regel: Untergrenze ≤ Blocker ≤ exaktes Optimum beim Abruf ≤ Regel beim Abruf.
- **Geschlossene Lücke** = (niedrigster Stapel − mit Schätzung) / (niedrigster Stapel − volles Wissen).

## Methodik

- **Live:** Stichprobe (20 bis 200 Buchten) aus den Reglern (Stapel 3 bis 6, Höhe 3 bis 5, Füllgrad 30 bis 80 %, Schätzfehler 0 bis 4, erste Bucht-Nummer): Mittel der Umlagerungen je Regel, geschlossene Lücke, Untergrenze bis 10 Container, exaktes Optimum bis 12 Container (Knotenlimit 100 000 je Bucht).
- **Vorberechnet** (`eas_bands.json`, erzeugt von `generate_precomputed.py`, unter fünf Minuten in mehreren Prozessen): sechs Zellen mit 300 Buchten für Kosten gegen den Schätzfehler (12 Stufen), zwei kleine Zellen mit 200 Buchten für Untergrenze und exaktes Optimum.
- Alle Kennzahlen sind **Mittel über feste Seeds** (Rauschen und Zufallsregel aus `random.Random(seed)`: deterministisch); es gibt keine Zeitmessung.
- **Abschnitte der App:** Ergebnis (live); eine Bucht von Hand (die erste Bucht der Stichprobe mit drei Regeln); wie viel der Lücke die Schätzung schließt; wie weit das volle Wissen von der Untergrenze entfernt ist; Grenzen; mathematische Formulierung.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Zufallsbuchten, nachgerechnet in `tests/test_claims.py`, `tests/test_presets.py` und `tests/test_oracle_einlagern_schaetzung_umstauen.py`.

**A: Umlagerungen beim Abruf gegen den Schätzfehler** (300 Buchten je Zelle, Mittel; σ in Vielfachen der Containerzahl)

| Zelle (Stapel × Höhe, Container) | zufällig | niedrigster Stapel | σ = 0 | σ = 0,05 | σ = 0,1 | σ = 0,2 | σ = 0,5 | σ = 1 | σ = 2 | σ = 4 | Kipppunkt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 × 4, 8 | 4,21 | 4,05 | 1,16 | 1,29 | 1,64 | 2,22 | 3,10 | 3,56 | 3,83 | 3,99 | nicht erreicht |
| 4 × 4, 10 | 4,49 | 4,11 | 0,58 | 0,73 | 1,25 | 2,07 | 3,05 | 3,73 | 4,09 | 4,23 | 3 |
| 4 × 4, 12 | 6,70 | 6,14 | 1,44 | 1,67 | 2,32 | 3,51 | 4,93 | 5,72 | 6,12 | 6,29 | 3 |
| 5 × 4, 14 | 6,64 | 6,23 | 0,73 | 1,16 | 1,94 | 3,02 | 4,72 | 5,66 | 6,15 | 6,32 | 3 |
| 6 × 4, 18 | 8,91 | 8,44 | 0,99 | 1,76 | 2,83 | 4,43 | 6,44 | 7,74 | 8,40 | 8,74 | 3 |
| 4 × 5, 14 | 9,09 | 8,42 | 2,43 | 2,86 | 3,70 | 5,06 | 6,86 | 7,97 | 8,29 | 8,72 | 3 |

**Geschlossener Anteil der Lücke** (niedrigster Stapel bis volles Wissen)

| Zelle | σ = 0,05 | σ = 0,1 | σ = 0,2 | σ = 0,5 | σ = 1 | σ = 2 | σ = 3 | σ = 4 |
|---|---|---|---|---|---|---|---|---|
| 3 × 4, 8 | 95 % | 83 % | 63 % | 33 % | 17 % | 8 % | 3 % | 2 % |
| 4 × 4, 10 | 96 % | 81 % | 58 % | 30 % | 11 % | 1 % | −3 % | −3 % |
| 4 × 4, 12 | 95 % | 81 % | 56 % | 26 % | 9 % | 0 % | −2 % | −3 % |
| 5 × 4, 14 | 92 % | 78 % | 58 % | 27 % | 10 % | 2 % | 0 % | −2 % |
| 6 × 4, 18 | 90 % | 75 % | 54 % | 27 % | 9 % | 1 % | −2 % | −4 % |
| 4 × 5, 14 | 93 % | 79 % | 56 % | 26 % | 8 % | 2 % | −3 % | −5 % |

Das Bild ist in allen Zellen gleich: Die geschlossene Lücke fällt von 100 % (σ = 0) über 90 bis 96 % (0,05) und rund 75 bis 83 % (0,1) auf gut die Hälfte (0,2), ein Viertel bis ein Drittel (0,5), unter 20 % (1) und 0 bis 8 % (2). Die Kosten wachsen in jeder Zelle mit jeder der 12 Stufen. Der niedrigste Stapel ist in jeder Zelle besser als der zufällige (4,05 gegen 4,21 bis 8,44 gegen 8,91). Der **Kipppunkt** (kleinster Schätzfehler der Stufen, bei dem die Schätzung nicht mehr besser ist als der niedrigste Stapel) liegt in fünf von sechs Zellen bei σ = 3, in 3 × 4 mit 8 Containern wird er bis σ = 4 nicht erreicht.

**B: Untergrenze der besten Ablage und exaktes Optimum** (200 Buchten je Zelle, Mittel)

| Zelle | Untergrenze | volles Wissen (Regel) | niedrigster Stapel | zufällig | Regel beim Abruf σ = 0,2 / 1 / 3 | exaktes Optimum nach der Ablage σ = 0,2 / 1 / 3 |
|---|---|---|---|---|---|---|
| 3 × 4, 8 Container | 0,90 | 1,23 | 4,08 | 4,19 | 2,30 / 3,65 / 4,01 | 2,28 / 3,59 / 3,91 |
| 4 × 4, 10 Container | 0,49 | 0,61 | 4,05 | 4,63 | 2,10 / 3,72 / 4,29 | 2,10 / 3,69 / 4,26 |

In allen 3 200 Paaren (2 Zellen · 200 Buchten · 8 Schätzfehler-Stufen) gilt Untergrenze ≤ exaktes Optimum ≤ Regel beim Abruf. Mit vollem Wissen liegt die Regel 0,34 (3 × 4) und 0,12 (4 × 4) über der Untergrenze (Differenzen aus den ungerundeten Mitteln), der niedrigste Stapel 3,18 und 3,56. Das exakte Optimum beim Abruf liegt höchstens 0,1 unter der Regel: Der Abruf nach „engster Passung“ ist hier fast optimal, der Verlust entsteht beim Einlagern.

| Frage | Befund |
|---|---|
| **Wie viel nützt die Schätzung?** | Bei σ = 0,2 schließt sie 54 bis 63 % der Lücke zwischen niedrigstem Stapel und vollem Wissen, bei σ = 0,1 75 bis 83 %, bei σ = 0,05 90 bis 96 %. |
| **Ab wann nützt sie nichts mehr?** | Bei σ = 2 nur noch 0 bis 8 %; bei σ = 3 ist sie in fünf von sechs Zellen schlechter als der niedrigste Stapel (Kipppunkt σ = 3); in der sechsten (3 × 4, 8 Container) bis σ = 4 nicht. |
| **Wie weit ist das volle Wissen von der Untergrenze?** | Nahe: 0,34 und 0,12 Umlagerungen darüber. Der niedrigste Stapel liegt 3,2 bis 3,6 darüber: **Fast die ganze Lücke ist Nichtwissen.** |
| **Hilft ein besserer Abruf?** | Kaum: Das exakte Optimum beim Abruf liegt höchstens 0,1 unter der Regel. |
| **Wächst der Effekt mit der Bucht?** | Nein: Die geschlossene Lücke bei σ = 0,2 liegt von 8 bis 18 Containern zwischen 54 und 63 %. Die absoluten Kosten wachsen mit der Containerzahl. |

**Presets** (Eigenschaften in `tests/test_presets.py`): „Alltag“ (4 × 4, 10 Container, σ = 0,2: 55 % der Lücke), „Volles Wissen“ (σ = 0: 0,65 gegen 4,02 des niedrigsten Stapels), „Schätzung wertlos“ (σ = 4: 4,31 gegen 4,02), „Kleine Bucht mit Untergrenze“ (3 × 4, 8 Container, σ = 0,1: Untergrenze 0,85, 76 %), „Große Bucht“ (6 × 4, 18 Container: 54 %).

**Korrektur gegenüber dem Plan:** Die Zahlen stimmen mit der Vormessung überein (Zählungen aus festen Seeds). Der Plan nannte 0,33 für den Abstand des vollen Wissens zur Untergrenze in 3 × 4; aus den ungerundeten Mitteln (1,235 − 0,895) sind es 0,335, die App zeigt kaufmännisch gerundet 0,34. Die Zelle 3 × 4 mit 8 Containern steht in zwei Tabellen mit leicht verschiedenen Zahlen für den niedrigsten Stapel (4,05 mit 300, 4,08 mit 200 Buchten): zwei verschieden große Stichproben derselben Buchten (die ersten 200 sind in den 300 enthalten).

## Ehrliche Grenzen

- **Gauß-Rauschen auf dem Rang,** unabhängig je Container und gleich groß; echte Schätzfehler sind oft systematisch (zu früh oder zu spät) und hängen an Gruppen. Die Messung gilt für dieses Rauschen.
- **Alle Ankünfte vor allen Abrufen.** Laufende Ankünfte und Abholungen im Wechsel (Fall-Demo Stapelplanung) sind nicht abgebildet; der Kipppunkt hier (σ ≈ 3) ist **nicht** der der Fall-Demo (andere Familie, anderes Maß, kein Vergleich).
- **Abruf nach der Regel „engste Passung“;** das exakte Optimum nur in den zwei kleinen Zellen (dort liegt es höchstens 0,1 darunter).
- **Untergrenze nur bis 10 Container:** Die Aufzählung der Zustände wächst schnell.
- **Zufällige Ankunftsreihenfolge:** Kommen die Container schon fast in der Reihenfolge der Abfahrt an, gewinnt jede Regel.
- **Nur die Zahl der Umlagerungen** (keine Kranzeit, keine Fahrwege; Brücke zur Linie „Zielfunktion“).
- **Kleine Stichproben:** 300 und 200 Buchten je Zelle; Differenzen von 0,02 bis 0,05 zwischen Stufen sind Rauschen.

## Verifikation

- **Kern:** Ankunftsreihenfolge und Rauschen deterministisch (Handwerte), Schätzung wächst linear mit σ, jede Einlege-Regel an Handbuchten ((1, 3), (2) gegen (1), (2, 3): 2 gegen 1 Umlagerungen; sortierbar: 0), Platzgrenzen, Abruf von Hand, Untergrenze der Ablage von Hand, exaktes Optimum von Hand.
- **Orakel:** Untergrenze der besten Ablage gegen eine **Aufzählung aller Platzierungen** (`itertools.product`) in 125 Buchten aus fünf Zellen; die Regel „engste Passung“ beim Einlegen gegen eine **ausgeschriebene zweite Umsetzung** für vier Schätzfehler in 90 Buchten; das exakte Optimum gegen eine **vollständige Rekursion** und die Kette Untergrenze ≤ Blocker ≤ exaktes Optimum ≤ Regel in 450 Buchten und Regeln; Eigenschaft: im Mittel volles Wissen < σ = 0,2 < σ = 1 < σ = 4, und σ = 0,2 besser, σ = 4 schlechter als der niedrigste Stapel.
- **Zahlen im README:** jede Zahl der Befunde in `tests/test_claims.py` (gespeicherte Bänder: Kosten steigen streng mit σ in allen 12 Stufen, geschlossener Anteil, Kipppunkte, Untergrenzen); eine Kostenzelle und eine Untergrenzenzelle werden frisch nachgerechnet (Zählungen, keine Zeiten).
- **Verdikte:** reine Funktionen, jede Schwelle (80 % und 40 % der Lücke einschließlich, Rauschen bei 1 − 0,2 und 1 − 0,6, eine Umlagerung Abstand zur Untergrenze) und jede genannte Zahl an von Hand gesetzten Werten (`tests/test_verdicts.py`).
- **Presets und Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), Inhalt (Kennzahlen je Preset, Tabellenzeilen, Hand-Bucht, Verlinkung der Fall-Demos), Layout, Footer, Laufzeit-Importe, Abbildungen (Farben, gesperrte Achsen, Kategorieachsen ohne `add_hline`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Aufbau nach DEMO-PLAYBOOK §2) |
| `generate_precomputed.py` | erzeugt `eas_bands.json` (Kosten gegen Schätzfehler, Untergrenze, exaktes Optimum) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt): streamlit, plotly |
| `eas_algorithm.py` | Einlegen (drei Regeln, Schätzung), Abruf, Untergrenze der Ablage, exaktes Optimum beim Abruf |
| `eas_bands.json` | vorberechnete Kennzahlen der festen Buchten je Zelle |
| `eas_constants.py` | Regler-Grenzen und -Stufen, Limits, Zellen, Schwellen, Farben, Presets |
| `eas_evaluation.py` | Stichprobe, Kennzahlen, Verdikte (reine Funktionen) |
| `eas_layout.py` | Fester Kopf (Stylesheet) |
| `eas_presets.py` | Permalink (auf Stufen gerückt), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `eas_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Behauptungen, Verdikte, Presets, Abbildungen, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Laufende Ankünfte und Abholungen** (Fall-Demo Stapelplanung) und **systematische Schätzfehler**.
- **Lernende Regeln und Schätzung mit Sicherheitszuschlag** (Stück 14).
- **Die Quellen** (TU Delft, FSMJ 2022) im Volltext.
- **PDF-Export:** nicht vorgesehen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

91 Tests, rund vier Minuten (die App-Tests rechnen die Stichproben live).

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
