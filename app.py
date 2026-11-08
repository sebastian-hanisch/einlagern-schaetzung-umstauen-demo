"""Einlagern: was ist eine Abfahrtsschätzung wert? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 12 der Reihe „Umstauen: Untergrenze und Suche“. Container kommen nacheinander an und müssen sofort auf einen Stapel; ihre Abfahrt ist nur geschätzt. Danach werden sie in der Reihenfolge
der wahren Abfahrt abgerufen, was darüber liegt, wird umgelagert. Die Demo misst, wie viel der Lücke zwischen „niedrigster Stapel“ (kein Wissen) und vollem Wissen die Schätzung schließt, ab
welchem Schätzfehler kein Vorteil mehr zu sehen ist und wie weit das volle Wissen von der Untergrenze der besten Ablage entfernt ist.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import eas_constants as C
from eas_algorithm import blockers, relocations
from eas_evaluation import (
    RULE_NAMES,
    Settings,
    analyse,
    bound_line,
    dec,
    key,
    load_bands,
    result_rows,
    sigma_key,
    sigma_text,
    percent_text,
    verdict_bound,
    verdict_kipp,
    verdict_sample,
)
from eas_layout import dunkles_design, kopf_css
from eas_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from eas_visualization import build_bay, build_closed, build_cost, build_rules

st.set_page_config(page_title="Einlagern mit Schätzung – Sebastian Hanisch", layout="wide")

TABLE_SIGMAS = (0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 4.0)


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _bands():
    return load_bands()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in eas_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📦 Einlagern: was ist eine Abfahrtsschätzung wert?")
st.markdown(
    """
Bisher war die Reihenfolge der Abfahrt **bekannt**. Hier ist sie beim **Einlagern** nur **geschätzt**: Die Container kommen nacheinander an und müssen **sofort** auf einen Stapel; danach werden sie in der Reihenfolge der **wahren** Abfahrt abgerufen, und was über dem nächsten liegt, wird **umgelagert**. Die Demo misst, **wie viel der Lücke** zwischen dem **niedrigsten Stapel** (kein Wissen) und dem **vollen Wissen** die Schätzung schließt, **ab welchem Schätzfehler** kein Vorteil mehr zu sehen ist und **wie weit das volle Wissen von der Untergrenze** der besten Ablage entfernt ist.

Die Fall-Demos [Stapelplanung](https://sebastianhanisch-stapelplanung-demo.streamlit.app/) (Block mit laufenden Ankünften und Abholungen, Kipppunkt des Schätzfehlers) und [Hofstellplatz](https://sebastianhanisch-hofstellplatz-demo.streamlit.app/) (vorausschauende Regel meist nicht besser als die naive) behandeln dieselbe Frage am Fall; ihre Zahlen stehen **dort**. Hier wird **vom Verfahren her** gemessen, mit der Untergrenze als Maßstab.

Weiter unten: die Abschnitte **🔬 Experiment** (eine Bucht von Hand, wie viel der Lücke die Schätzung schließt, wie weit das volle Wissen von der Untergrenze entfernt ist), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Dies ist das zwölfte Stück der Reihe „Umstauen: Untergrenze und Suche“.
"""
)

with st.expander("So wird gemessen", expanded=True):
    st.markdown(
        """
1. **Bucht:** *Stapel* Stapel der Höchsthöhe *H*, *N* Container (Füllgrad in Prozent der Plätze, es bleibt mindestens eine Stapelhöhe frei). Die Container kommen in zufälliger Reihenfolge an; jeder hat eine **wahre Abfahrtsnummer** 1 bis *N* (1 fährt zuerst ab).
2. **Einlegen:** jeder Container wird beim Eintreffen sofort auf einen Stapel mit Platz gesetzt. Regeln: **zufälliger Stapel**, **niedrigster Stapel** (die wenigsten Container, keine Schätzung nötig), **engste Passung nach Schätzung** (Stück 1 auf geschätzten Nummern).
3. **Schätzung:** wahre Nummer + σ · *N* · *z* mit einer standardnormalen Zufallszahl *z* je Container. σ = 0 ist **volles Wissen**; σ = 0,2 heißt: typische Abweichung rund 20 % der Containerzahl.
4. **Abruf:** in der Reihenfolge der wahren Abfahrt; liegt der nächste nicht oben, werden die Container darüber umgelagert (restricted, Regel „engste Passung“ nach den **wahren** Nummern). **Kosten = Zahl der Umlagerungen.**
5. **Untergrenze der besten Ablage:** die kleinste Zahl von Blockern in der fertigen Bucht über **alle** möglichen Platzierungen der Ankömmlinge. Jede Umlagerung braucht einen Blocker, also kostet **keine** Einlege-Regel weniger.
6. **Geschlossene Lücke** = (niedrigster Stapel − mit Schätzung) / (niedrigster Stapel − volles Wissen).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Bucht**")
    stacks = st.slider("Stapel", *bounds("stacks_slider"), key="stacks_slider", help="Wie viele Stapel die Bucht hat.")
    height = st.slider("Höchsthöhe", *bounds("height_slider"), key="height_slider", help="So viele Container passen auf einen Stapel.")
    fill = st.slider("Füllgrad (%)", *bounds("fill_slider"), key="fill_slider", step=5, help="Anteil der Plätze, der mit Containern belegt wird; es bleibt mindestens eine Stapelhöhe frei.")
    st.markdown("**Schätzung**")
    sigma = st.select_slider("Schätzfehler σ", options=C.SIGMA_OPTIONS, key="sigma_slider", format_func=sigma_text,
                             help="Streuung des Schätzfehlers in Vielfachen der Containerzahl. 0 = volles Wissen.")
    st.markdown("**Stichprobe**")
    bays = st.select_slider("Zahl der Buchten", options=C.BAY_OPTIONS, key="bays_slider", help="So viele Buchten gehören zur Stichprobe.")
    seed = st.number_input("Erste Bucht-Nummer (Seed)", *bounds("seed_input"), key="seed_input", step=1, help="Die Stichprobe besteht aus den Buchten Nummer Seed bis Seed + Buchten − 1.")
    st.button("🎲 Neue Stichprobe würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"stacks_slider": int(stacks), "height_slider": int(height), "fill_slider": int(fill), "sigma_slider": float(sigma), "bays_slider": int(bays), "seed_input": int(seed)})

settings = Settings(int(stacks), int(height), int(fill), float(sigma), int(bays), int(seed))
with st.spinner("Lege die Stichprobe ein und rufe sie ab …"):
    a = _analysis(settings)
s = a.stats

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Container je Bucht", a.n, delta=f"{settings.stacks} × {settings.height}, {settings.bays} Buchten", delta_color="off")
m2.metric("Volles Wissen", dec(s["full"]), delta="Umlagerungen", delta_color="off", help="Engste Passung nach den wahren Nummern (Schätzfehler 0), Mittel über die Buchten.")
m3.metric("Mit Schätzung", dec(s["tight"]), delta=f"σ = {sigma_text(settings.sigma)}", delta_color="off", help="Engste Passung nach den geschätzten Nummern.")
m4.metric("Niedrigster Stapel", dec(s["lowest"]), delta=f"zufällig: {dec(s['random'])}", delta_color="off", help="Kein Wissen nötig: der Stapel mit den wenigsten Containern.")
m5.metric("Geschlossene Lücke", "–" if s["closed"] is None else percent_text(s["closed"]), delta="niedrigster Stapel bis volles Wissen", delta_color="off")
st.plotly_chart(build_rules(s), width="stretch", key="chart_rules")
table = ["| Einlege-Regel | Umlagerungen beim Abruf (Mittel) |", "|---|---|"]
for r in result_rows(s):
    table.append(f"| {r['name']} | {r['value']} |")
st.markdown("\n".join(table))
st.caption("Alle Werte sind Mittel über die Stichprobe (feste Seeds); keine Zeitmessung.")

st.markdown("## ❓ Kernfrage: Wie viel nützt die Schätzung?")
kind, text = verdict_sample(s, f"{settings.stacks} Stapel × Höhe {settings.height}, {a.n} Container", settings.sigma)
getattr(st, kind)(text)
line = bound_line(s)
if line:
    st.info(line)

st.markdown("---")

# --- Experiment: eine Bucht von Hand ----------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Eine Bucht von Hand")
ex = a.example
st.caption(f"Die erste Bucht der Stichprobe (Nummer {settings.seed}): Die Container kommen in dieser Reihenfolge an, die Zahl ist die **wahre Abfahrtsnummer** (1 = fährt zuerst ab): "
           + ", ".join(str(c) for c in ex["arrivals"]) + ". Die geschätzten Werte: " + ", ".join(dec(e, 1) for e in ex["estimates"]) + ".")
c1, c2, c3 = st.columns(3)
for col, rule, label in ((c1, "lowest", "Niedrigster Stapel"), (c2, "tight", f"Mit Schätzung (σ = {sigma_text(settings.sigma)})"), (c3, "full", "Volles Wissen")):
    bay = ex["bays"][rule]
    col.markdown(f"**{label}:** {blockers(bay)} Blocker, **{relocations(bay, settings.height)} Umlagerungen**")
    col.plotly_chart(build_bay(bay, settings.height), width="stretch", key=f"chart_bay_{rule}")
st.caption("Rot: Blocker (liegen über einem früher abzufahrenden Container), grau-blau: alle übrigen. Jeder Blocker muss beim Abruf mindestens einmal bewegt werden.")

st.markdown("---")

# --- Experiment: wie viel der Lücke schließt die Schätzung ----------------------------------------------------------------------------------

bands = _bands()
sig, lb = bands["sigma"], bands["lb"]
st.subheader("🔬 Experiment: Wie viel der Lücke schließt die Schätzung?")
st.caption(f"Je Zelle {C.SIGMA_BAYS} feste Buchten, vorberechnet (`generate_precomputed.py`). Umlagerungen beim Abruf (Mittel); **Kipppunkt** = kleinster Schätzfehler der Stufen, bei dem die Schätzung nicht mehr besser ist "
           "als der niedrigste Stapel.")
ta = ["| Zelle (Stapel × Höhe, Container) | zufällig | niedrigster Stapel | " + " | ".join(f"σ = {sigma_text(x)}" for x in TABLE_SIGMAS) + " | Kipppunkt |", "|---|---|---|" + "---|" * len(TABLE_SIGMAS) + "---|"]
for s_, h_, n_ in C.SIGMA_CELLS:
    c = sig[key(s_, h_, n_)]
    ta.append(f"| {s_} × {h_}, {n_} | {dec(c['random'])} | {dec(c['lowest'])} | " + " | ".join(dec(c["tight"][sigma_key(x)]) for x in TABLE_SIGMAS) + f" | {'nicht erreicht' if c['kipp'] is None else sigma_text(c['kipp'])} |")
st.markdown("\n".join(ta))
st.markdown("**Geschlossener Anteil der Lücke** (niedrigster Stapel bis volles Wissen):")
tb = ["| Zelle | " + " | ".join(f"σ = {sigma_text(x)}" for x in TABLE_SIGMAS) + " |", "|---|" + "---|" * len(TABLE_SIGMAS)]
for s_, h_, n_ in C.SIGMA_CELLS:
    c = sig[key(s_, h_, n_)]
    tb.append(f"| {s_} × {h_}, {n_} | " + " | ".join(percent_text(c["closed"][sigma_key(x)]) for x in TABLE_SIGMAS) + " |")
st.markdown("\n".join(tb))
st.plotly_chart(build_closed(sig), width="stretch", key="chart_closed")
here_key = key(settings.stacks, settings.height, a.n)
st.markdown(f"**{settings.stacks} × {settings.height} mit {a.n} Containern (Ihre Einstellung):**")
if here_key in sig:
    kind, text = verdict_kipp(sig[here_key], f"{settings.stacks} × {settings.height}, {a.n} Container")
    getattr(st, kind)(text)
else:
    st.info(f"Für {settings.stacks} × {settings.height} mit {a.n} Containern wurde der Schätzfehler nicht vorberechnet; die Tabelle zeigt sechs Zellen.")

st.markdown("---")

# --- Experiment: Untergrenze der besten Ablage -----------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie weit ist das volle Wissen von der Untergrenze?")
st.caption(f"Zwei kleine Zellen, je {C.LB_BAYS} Buchten: die Untergrenze der besten Ablage (kleinste Blockerzahl über **alle** Platzierungen) und das **exakte** Optimum beim Abruf nach der Ablage mit Schätzung "
           "(Suche aus Stück 5 bis 9). Es gilt Untergrenze ≤ exaktes Optimum ≤ Regel beim Abruf in jeder Bucht.")
for s_, h_, n_ in C.LB_CELLS:
    c = lb[key(s_, h_, n_)]
    st.markdown(f"**{s_} Stapel × Höhe {h_}, {n_} Container:** Untergrenze {dec(c['lb'])}, niedrigster Stapel {dec(c['lowest'])}, zufälliger Stapel {dec(c['random'])}")
    tc = ["| Schätzfehler σ | " + " | ".join(sigma_text(x) for x in C.LB_SIGMAS) + " |", "|---|" + "---|" * len(C.LB_SIGMAS),
          "| engste Passung nach Schätzung | " + " | ".join(dec(c["greedy"][sigma_key(x)]) for x in C.LB_SIGMAS) + " |",
          "| exaktes Optimum nach der Ablage | " + " | ".join(dec(c["exact"][sigma_key(x)]) for x in C.LB_SIGMAS) + " |"]
    st.markdown("\n".join(tc))
    st.plotly_chart(build_cost(c), width="stretch", key=f"chart_cost_{s_}_{h_}_{n_}")
    kind, text = verdict_bound(c, f"{s_} × {h_}, {n_} Container")
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Gauß-Rauschen auf dem Rang** | Der Schätzfehler ist hier unabhängig je Container und gleich groß; echte Schätzfehler sind oft systematisch (zu früh oder zu spät) und hängen an Gruppen. Die Messung gilt für dieses Rauschen. | – |
| **Alle Ankünfte vor allen Abrufen** | Die Container werden erst eingelagert, dann abgerufen. Laufende Ankünfte und Abholungen im Wechsel (wie in der Fall-Demo Stapelplanung) sind nicht abgebildet. | Fall-Demo Stapelplanung |
| **Abruf nach der Regel „engste Passung“** | Beim Abruf wird nicht optimal umgelagert; nur in den zwei kleinen Zellen wird zusätzlich das exakte Optimum gerechnet (es liegt im Mittel höchstens 0,1 unter der Regel). | Stück 1, 5 bis 9 |
| **Untergrenze nur bis 10 Container** | Die kleinste Blockerzahl über alle Platzierungen wird durch Aufzählen der Zustände gerechnet und wächst schnell; darüber wird sie nicht gerechnet. | – |
| **Zufällige Ankunftsreihenfolge** | Die wahren Abfahrtsnummern sind zufällig verteilt; bei einer Ankunftsreihenfolge, die schon fast der Abfahrt gleicht, dürften alle Regeln besser abschneiden (nicht gemessen). | – |
| **Nur die Zahl der Umlagerungen** | Kranzeit, Fahrwege und Zeitfenster zählen nicht (Brücke zur Linie „Zielfunktion“). | Zielfunktionsdesign |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben:** $S$ Stapel mit Höchsthöhe $H$, $N$ Container, die in der Reihenfolge $i = 1, \dots, N$ eintreffen; der $i$-te hat die **wahre Abfahrtsnummer** $r_i$ (eine Permutation von $1, \dots, N$; 1 fährt zuerst ab). Jeder Container wird beim Eintreffen auf einen Stapel mit Platz gesetzt und bleibt dort, bis alle eingelagert sind.

**Schätzung.** $\hat r_i = r_i + \sigma\, N\, z_i$ mit $z_i \sim \mathcal N(0, 1)$ unabhängig. $\sigma = 0$ ist volles Wissen.

**Regeln.** *Zufällig*: gleichverteilt über die Stapel mit Platz. *Niedrigster Stapel*: die wenigsten Container. *Engste Passung nach Schätzung*: Sei $m_k$ der kleinste Schätzwert im Stapel $k$ ($\infty$, wenn leer). Unter den Stapeln mit $m_k > \hat r_i$ wird der mit dem kleinsten $m_k$ gewählt, gibt es keinen, der mit dem größten $m_k$.

**Kosten.** Danach werden die Container in der Reihenfolge $r = 1, \dots, N$ abgerufen; liegt $r$ nicht oben, werden die Container darüber nacheinander auf andere Stapel mit Platz gesetzt (restricted). Kosten $C$ = Zahl dieser Umlagerungen.

**Untergrenze der besten Ablage.** Ein Container $c$ ist ein **Blocker**, wenn im selben Stapel unter ihm ein Container mit kleinerer Nummer liegt. Jeder Blocker muss mindestens einmal umgelagert werden. Sei $B(P)$ die Blockerzahl der fertigen Bucht bei der Platzierung $P$ und
$$L = \min_P B(P)$$
über alle zulässigen Platzierungen. Dann gilt für **jede** Einlege-Regel (auch eine, die die wahren Nummern kennt) $L \le B(P) \le \text{OPT}(P) \le C$.

**Geschlossene Lücke.** Mit $\bar C_{\text{niedrig}}$, $\bar C_{\hat\sigma}$ und $\bar C_0$ den mittleren Kosten von niedrigstem Stapel, Schätzung mit Fehler $\hat\sigma$ und vollem Wissen:
$$g(\hat\sigma) = \frac{\bar C_{\text{niedrig}} - \bar C_{\hat\sigma}}{\bar C_{\text{niedrig}} - \bar C_0}.$$
$g = 1$: Die Schätzung ist so gut wie volles Wissen; $g = 0$: so gut wie der niedrigste Stapel; $g < 0$: schlechter.

**Literatur.** Einlagern unter unsicherer Abfahrt ist ein eigener Strang der Container-Stapelung (zum Beispiel „Stacking under uncertainty“, TU Delft; datengetriebene Online-Strategien); diese Quellen sind aus Suchtreffern bekannt und **nicht gelesen**. Die hier genannten Zahlen sind eigene Messungen an Zufallsbuchten.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
