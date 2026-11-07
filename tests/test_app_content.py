"""Inhalt der App an festen Fällen (DEMO-PLAYBOOK §12): was im Ergebnis, in den Tabellen und in den Verdikten steht."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(preset=None):
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    if preset:
        at.sidebar.button(key=f"preset_{preset}").click().run()
        assert not at.exception, [str(e) for e in at.exception]
    return at


def _text(at):
    return "\n".join(e.value for kind in (at.markdown, at.caption, at.info, at.success, at.warning) for e in kind)


def _metrics(at):
    return {m.label: (m.value, m.delta) for m in at.metric}


def test_default_page_has_the_sections_and_the_default_result():
    at = _run()
    subs = [s.value for s in at.subheader]
    assert [s for s in subs if s.startswith("🔬")] == ["🔬 Experiment: Eine Bucht von Hand", "🔬 Experiment: Wie viel der Lücke schließt die Schätzung?",
                                                       "🔬 Experiment: Wie weit ist das volle Wissen von der Untergrenze?"]
    assert "🚧 Wo die Annahmen enden" in subs
    m = _metrics(at)
    assert m["Container je Bucht"] == ("10", "4 × 4, 100 Buchten") and m["Volles Wissen"][0] == "0,65" and m["Mit Schätzung"] == ("2,15", "σ = 0,2")
    assert m["Niedrigster Stapel"] == ("4,02", "zufällig: 4,79") and m["Geschlossene Lücke"][0] == "55 %"
    assert any(i.value.startswith("4 Stapel × Höhe 4, 10 Container: Der niedrigste Stapel kostet im Mittel 4,02 Umlagerungen") and "schließt 55 % der Lücke. Sie trägt zum Teil." in i.value for i in at.info)


def test_default_page_tables_quote_the_stored_numbers():
    text = _text(_run())
    assert "| Untergrenze der besten Ablage | 0,49 |" in text and "| engste Passung nach Schätzung | 2,15 |" in text and "| zufälliger Stapel | 4,79 |" in text
    assert "| 3 × 4, 8 | 4,21 | 4,05 | 1,16 | 1,29 | 1,64 | 2,22 | 3,10 | 3,56 | 3,83 | 3,99 | nicht erreicht |" in text
    assert "| 4 × 4, 10 | 4,49 | 4,11 | 0,58 | 0,73 | 1,25 | 2,07 | 3,05 | 3,73 | 4,09 | 4,23 | 3 |" in text
    assert "| 4 × 4, 10 | 100 % | 96 % | 81 % | 58 % | 30 % | 11 % | 1 % | -3 % |" in text
    assert "| engste Passung nach Schätzung | 0,61 | 1,27 | 2,10 | 3,04 | 3,72 | 4,17 | 4,29 | 4,34 |" in text and "| exaktes Optimum nach der Ablage | 1,23 | 1,76 | 2,28 | 3,18 | 3,59 | 3,84 | 3,91 | 3,93 |" in text
    assert "**3 Stapel × Höhe 4, 8 Container:** Untergrenze 0,90, niedrigster Stapel 4,08, zufälliger Stapel 4,19" in text


def test_default_page_verdicts_and_the_hand_section():
    text = _text(_run())
    assert "4 × 4, 10 Container: Der Kipppunkt liegt zwischen 2 und 3: Dort kostet die Regel mit Schätzung (4,20) so viel wie oder mehr als der niedrigste Stapel (4,11)." in text
    assert "Mit vollem Wissen fehlen 0,12 bis zur Untergrenze, ohne Wissen 3,56. Das volle Wissen liegt nahe an der Untergrenze." in text
    assert "8, 9, 2, 6, 4, 5, 3, 1, 10, 7" in text and "**Niedrigster Stapel:** 3 Blocker, **3 Umlagerungen**" in text and "**Volles Wissen:** 0 Blocker, **0 Umlagerungen**" in text
    assert "https://sebastianhanisch-stapelplanung-demo.streamlit.app/" in text and "https://sebastianhanisch-hofstellplatz-demo.streamlit.app/" in text


def test_full_knowledge_preset_shows_the_success_verdict():
    at = _run("Volles Wissen (Schätzfehler 0)")
    assert _metrics(at)["Geschlossene Lücke"][0] == "100 %" and _metrics(at)["Mit Schätzung"] == ("0,65", "σ = 0")
    assert any(s.value.endswith("Die Schätzung schließt 100 % der Lücke. Sie trägt.") for s in at.success)


def test_worthless_estimate_preset_shows_the_warning():
    at = _run("Schätzung wertlos (Schätzfehler 4)")
    assert _metrics(at)["Mit Schätzung"] == ("4,31", "σ = 4") and _metrics(at)["Geschlossene Lücke"][0] == "-9 %"
    assert any(w.value.endswith("Sie ist schlechter als der niedrigste Stapel.") for w in at.warning)


def test_large_bay_preset_has_no_lower_bound_line():
    at = _run("Große Bucht (6 Stapel, Höhe 4)")
    text = _text(at)
    assert _metrics(at)["Container je Bucht"][0] == "18" and "| Untergrenze der besten Ablage | nicht gerechnet |" in text and "Untergrenze der besten Ablage (Blocker der besten fertigen Bucht)" not in text
    assert "Für 6 × 4 mit 18 Containern" not in text                                         # die Zelle 6 × 4 mit 18 Containern ist vorberechnet


@pytest.mark.parametrize("stacks,height,fill", [(3, 3, 30), (5, 5, 80)])
def test_settings_without_stored_bands_do_not_crash(stacks, height, fill):
    at = _run()
    at.sidebar.slider(key="stacks_slider").set_value(stacks).run()
    at.sidebar.slider(key="height_slider").set_value(height).run()
    at.sidebar.slider(key="fill_slider").set_value(fill).run()
    assert not at.exception
    assert "wurde der Schätzfehler nicht vorberechnet" in _text(at)
