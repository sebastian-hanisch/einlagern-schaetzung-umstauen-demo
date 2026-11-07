"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STACKS_MIN, STACKS_MAX, DEFAULT_STACKS = 3, 6, 4          # Zahl der Stapel
HEIGHT_MIN, HEIGHT_MAX, DEFAULT_HEIGHT = 3, 5, 4          # Höchsthöhe eines Stapels
FILL_MIN, FILL_MAX, DEFAULT_FILL = 30, 80, 60             # Füllgrad in Prozent der Plätze; Container = Füllgrad * Plätze, höchstens Plätze − Höchsthöhe, mindestens 2
SIGMA_OPTIONS = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)     # Streuung des Schätzfehlers in Vielfachen der Containerzahl (Stufen des Reglers)
DEFAULT_SIGMA = 0.2
BAY_OPTIONS = (20, 50, 100, 200)                          # Zahl der Buchten einer Stichprobe (Stufen des Reglers)
DEFAULT_BAYS = 100
DEFAULT_SEED = 0                                          # erste Bucht-Nummer der Stichprobe: Seeds seed bis seed + Buchten − 1
SEED_MAX = 999999

LB_MAX_CONTAINERS = 10                                    # die Untergrenze (beste Ablage) wird live nur bis zu dieser Containerzahl gerechnet
EXACT_MAX_CONTAINERS = 12                                 # das exakte Relocation-Optimum wird live nur bis zu dieser Containerzahl gerechnet
EXACT_CAP = 100_000                                       # Knotenlimit der Suche je Bucht

# Zellen der vorberechneten Tabellen: (Stapel, Höchsthöhe, Container). Seeds ab 0.
SIGMA_CELLS = ((3, 4, 8), (4, 4, 10), (4, 4, 12), (5, 4, 14), (6, 4, 18), (4, 5, 14))      # A: Kosten gegen Schätzfehler
SIGMA_BAYS = 300
LB_CELLS = ((3, 4, 8), (4, 4, 10))                        # B: Untergrenze und exaktes Optimum
LB_BAYS = 200
LB_SIGMAS = (0.0, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0, 4.0)
BAND_EXACT_CAP = 200_000

# Schwellen der Verdikte
CLOSED_BIG = 0.8                                          # „die Schätzung trägt“: Anteil der Lücke (niedrigster Stapel bis volles Wissen), den die Schätzung schließt, mindestens so groß
CLOSED_HALF = 0.4                                         # „trägt zum Teil“; darunter „trägt kaum“
GAP_NEAR = 1.0                                            # „nahe an der Untergrenze“: Kosten mit vollem Wissen höchstens so viel über der Untergrenze (Umlagerungen)

COLOR_CELL = "#7a8fa6"
COLOR_BLOCK = "#b5545a"        # blockierend (liegt über einem früher abzufahrenden)
COLOR_TARGET = "#2F6B65"       # nächster Abruf
COLOR_RULES = {"random": "#7a8fa6", "lowest": "#d9822b", "tight": "#2F6B65", "full": "#1c4742"}
COLOR_LB = "#4c78a8"

# Presets (Eigenschaften in tests/test_presets.py)
PRESETS = {
    "Alltag (4 Stapel, Höhe 4, Schätzfehler 0,2)": {"stacks": 4, "height": 4, "fill": 60, "sigma": 0.2, "bays": 100, "seed": 0},
    "Volles Wissen (Schätzfehler 0)": {"stacks": 4, "height": 4, "fill": 60, "sigma": 0.0, "bays": 100, "seed": 0},
    "Schätzung wertlos (Schätzfehler 4)": {"stacks": 4, "height": 4, "fill": 60, "sigma": 4.0, "bays": 100, "seed": 0},
    "Kleine Bucht mit Untergrenze (3 Stapel, 8 Container)": {"stacks": 3, "height": 4, "fill": 65, "sigma": 0.1, "bays": 100, "seed": 0},
    "Große Bucht (6 Stapel, Höhe 4)": {"stacks": 6, "height": 4, "fill": 75, "sigma": 0.2, "bays": 100, "seed": 0},
}
PRESET_HELP = {
    "Alltag (4 Stapel, Höhe 4, Schätzfehler 0,2)": "10 Container: Eine Rangabweichung von rund 20 % der Containerzahl schließt gut die Hälfte der Lücke zwischen „niedrigster Stapel“ und vollem Wissen.",
    "Volles Wissen (Schätzfehler 0)": "10 Container: Mit den wahren Abfahrtsnummern kostet das Einlagern nach engster Passung im Mittel gut eine halbe Umlagerung, der niedrigste Stapel rund vier.",
    "Schätzung wertlos (Schätzfehler 4)": "10 Container: Bei einer Streuung von vier Containerzahlen ist die Schätzung nicht besser als der niedrigste Stapel (sie liegt darüber).",
    "Kleine Bucht mit Untergrenze (3 Stapel, 8 Container)": "8 Container: Die Untergrenze (beste Ablage) und das exakte Optimum beim Abruf werden live gerechnet.",
    "Große Bucht (6 Stapel, Höhe 4)": "18 Container: Der Effekt der Schätzung bleibt bei größeren Buchten gleich groß; die Untergrenze wird hier nicht gerechnet.",
}
