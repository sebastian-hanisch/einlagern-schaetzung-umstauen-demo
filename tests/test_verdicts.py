"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import eas_constants as C
import eas_evaluation as ev


def _s(lowest=4.0, tight=2.0, full=1.0, random=4.5, **extra):
    s = {"n": 100, "random": random, "lowest": lowest, "tight": tight, "full": full, "blockers": 2.0, "closed": ev.closed_share(lowest, tight, full)}
    s.update(extra)
    return s


def test_sample_verdict_three_states_and_numbers():
    kind, text = ev.verdict_sample(_s(4.0, 1.5, 1.0), "4 Stapel × Höhe 4, 10 Container", 0.1)
    assert kind == "success" and text == ("4 Stapel × Höhe 4, 10 Container: Der niedrigste Stapel kostet im Mittel 4 Umlagerungen, die Regel mit vollem Wissen 1, mit Schätzfehler 0,1 1,50. "
                                          "Die Schätzung schließt 83 % der Lücke. Sie trägt.")
    kind, text = ev.verdict_sample(_s(4.0, 2.5, 1.0), "x", 0.2)
    assert kind == "info" and text.endswith("Die Schätzung schließt 50 % der Lücke. Sie trägt zum Teil.")
    kind, text = ev.verdict_sample(_s(4.0, 3.5, 1.0), "x", 0.5)
    assert kind == "warning" and text.endswith("Die Schätzung schließt 17 % der Lücke. Sie trägt kaum.")
    kind, text = ev.verdict_sample(_s(4.0, 4.3, 1.0), "x", 4.0)
    assert kind == "warning" and text.endswith("Die Schätzung schließt -10 % der Lücke. Sie ist schlechter als der niedrigste Stapel.")


def test_sample_verdict_thresholds_are_inclusive_and_float_safe():
    assert ev.verdict_sample(_s(100.0, 100.0 - 80.0, 0.0), "x", 0.1)[0] == "success" and C.CLOSED_BIG == 0.8       # genau 80 % zählt als „trägt“
    assert ev.verdict_sample(_s(1.0, 0.2, 0.0), "x", 0.1)[0] == "success"                                            # 1 − 0,2 = 0,8 (binär 0,8 − ε): Toleranz
    assert ev.verdict_sample(_s(100.0, 100.0 - 79.0, 0.0), "x", 0.1)[0] == "info"
    assert ev.verdict_sample(_s(100.0, 100.0 - 40.0, 0.0), "x", 0.1)[0] == "info" and C.CLOSED_HALF == 0.4          # genau 40 % zählt als „zum Teil“
    assert ev.verdict_sample(_s(1.0, 0.6, 0.0), "x", 0.1)[0] == "info"                                              # 1 − 0,6 = 0,4 mit Rauschen
    assert ev.verdict_sample(_s(100.0, 100.0 - 39.0, 0.0), "x", 0.1)[0] == "warning"


def test_sample_verdict_without_a_gap():
    kind, text = ev.verdict_sample(_s(1.0, 1.2, 1.0), "x", 0.2)
    assert kind == "info" and text.endswith("Hier gibt es keine Lücke: Das volle Wissen ist nicht besser als der niedrigste Stapel.") and "schließt" not in text


def test_bound_line_and_result_rows():
    assert ev.bound_line(_s()) is None
    s = _s(lb=0.49, exact=2.04)
    assert ev.bound_line(s) == ("Untergrenze der besten Ablage (Blocker der besten fertigen Bucht): im Mittel 0,49 Umlagerungen; Regel mit vollem Wissen 1; "
                                "exaktes Optimum nach der Ablage mit Schätzung 2,04 (Regel beim Abruf 2).")
    assert ev.bound_line(_s(lb=0.5)).endswith("Regel mit vollem Wissen 1.")
    rows = ev.result_rows(s)
    assert [r["name"] for r in rows] == ["Untergrenze der besten Ablage", "engste Passung mit vollem Wissen", "engste Passung nach Schätzung", "niedrigster Stapel", "zufälliger Stapel"]
    assert [r["value"] for r in rows] == ["0,49", "1", "2", "4", "4,50"] and ev.result_rows(_s())[0]["value"] == "nicht gerechnet"


def _sig(kipp, lowest=4.0, tight_at=None):
    tight = {ev.sigma_key(x): 1.0 for x in C.SIGMA_OPTIONS}
    tight.update(tight_at or {})
    return {"n": 300, "lowest": lowest, "random": 4.5, "tight": tight, "kipp": kipp}


def test_kipp_verdict_states_and_numbers():
    kind, text = ev.verdict_kipp(_sig(None), "3 × 4, 8 Container")
    assert kind == "info" and text == ("3 × 4, 8 Container: Bis zum Schätzfehler 4 kostet die Regel mit Schätzung weniger als der niedrigste Stapel (4 Umlagerungen); "
                                       "einen Kipppunkt gibt es im untersuchten Bereich nicht.")
    kind, text = ev.verdict_kipp(_sig(3.0, tight_at={"3": 4.2}), "4 × 4, 10 Container")
    assert kind == "warning" and text == ("4 × 4, 10 Container: Der Kipppunkt liegt zwischen 2 und 3: Dort kostet die Regel mit Schätzung (4,20) so viel wie oder mehr als der niedrigste Stapel (4).")
    kind, text = ev.verdict_kipp(_sig(0.0, tight_at={"0": 4.0}), "x")
    assert kind == "warning" and "schon bei 0" in text
    assert ev.verdict_kipp(_sig(0.05, tight_at={"0.05": 4.1}), "x")[1].count("zwischen 0 und 0,05") == 1


def _lb(lb=0.49, full=0.61, lowest=4.05):
    return {"n": 200, "lb": lb, "lowest": lowest, "random": 4.6, "greedy": {"0": full}, "exact": {"0": full}}


def test_bound_verdict_two_states_and_numbers():
    kind, text = ev.verdict_bound(_lb(), "4 × 4, 10 Container")
    assert kind == "success" and text == ("4 × 4, 10 Container: Die Untergrenze der besten Ablage liegt bei 0,49 Umlagerungen, die Regel mit vollem Wissen bei 0,61, der niedrigste Stapel bei 4,05: "
                                          "Mit vollem Wissen fehlen 0,12 bis zur Untergrenze, ohne Wissen 3,56. Das volle Wissen liegt nahe an der Untergrenze.")
    assert ev.verdict_bound(_lb(0.0, 1.0), "x")[0] == "success" and C.GAP_NEAR == 1.0                                # genau eine Umlagerung Abstand zählt als nahe
    assert ev.verdict_bound(_lb(0.1, 1.1), "x")[0] == "success"                                                      # 1,1 − 0,1 = 1,0000000000000002: Toleranz
    kind, text = ev.verdict_bound(_lb(0.0, 1.01), "x")
    assert kind == "info" and text.endswith("Das volle Wissen liegt noch deutlich über der Untergrenze.")
