"""Presets: jede Einstellung hat die Eigenschaft, für die sie steht (DEMO-PLAYBOOK §12), und die Hilfetexte nennen nur gemessene Zahlen."""

import pytest

import eas_constants as C
import eas_evaluation as ev
import eas_presets as P


def _analyse(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["stacks"], p["height"], p["fill"], p["sigma"], p["bays"], p["seed"]))


def test_every_preset_is_inside_the_slider_bounds_and_on_a_step_and_has_help():
    for name, p in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            lo, hi = P.bounds(state_key)
            assert lo <= p[key] <= hi and P.snap(state_key, p[key]) == p[key], (name, key)
    assert set(C.PRESET_HELP) == set(C.PRESETS) and all(C.PRESET_HELP.values())


def test_everyday_preset_closes_the_gap_by_half():
    a = _analyse("Alltag (4 Stapel, Höhe 4, Schätzfehler 0,2)")
    s = a.stats
    assert a.n == 10 and s["n"] == 100 and s["lowest"] == pytest.approx(4.02) and s["tight"] == pytest.approx(2.15) and s["full"] == pytest.approx(0.65) and s["random"] == pytest.approx(4.79)
    assert round(s["closed"], 3) == 0.555 and ev.verdict_sample(s, "x", 0.2)[0] == "info" and s["lb"] == pytest.approx(0.49) and s["lb_violations"] == 0 and s["exact"] == pytest.approx(2.15)


def test_full_knowledge_preset_closes_the_whole_gap():
    s = _analyse("Volles Wissen (Schätzfehler 0)").stats
    assert s["tight"] == s["full"] == pytest.approx(0.65) and s["closed"] == 1.0 and ev.verdict_sample(s, "x", 0.0)[0] == "success"


def test_worthless_estimate_preset_is_worse_than_the_lowest_stack():
    s = _analyse("Schätzung wertlos (Schätzfehler 4)").stats
    assert s["tight"] == pytest.approx(4.31) and s["lowest"] == pytest.approx(4.02) and s["tight"] > s["lowest"] and round(s["closed"], 3) == -0.086
    assert ev.verdict_sample(s, "x", 4.0) == ("warning", ev.verdict_sample(s, "x", 4.0)[1]) and ev.verdict_sample(s, "x", 4.0)[1].endswith("Im Mittel ist sie schlechter als der niedrigste Stapel.")


def test_small_bay_preset_has_the_bounds_and_the_exact_optimum():
    a = _analyse("Kleine Bucht mit Untergrenze (3 Stapel, 8 Container)")
    s = a.stats
    assert a.n == 8 and s["lb"] == pytest.approx(0.85) and s["full"] == pytest.approx(1.17) and s["tight"] == pytest.approx(1.86) and s["exact_n"] == 100 and s["exact_violations"] == 0
    assert a.example["arrivals"] == [5, 2, 6, 3, 1, 4, 8, 7]


def test_large_bay_preset_has_no_lower_bound():
    a = _analyse("Große Bucht (6 Stapel, Höhe 4)")
    assert a.n == 18 and "lb" not in a.stats and "exact" not in a.stats and round(a.stats["closed"], 3) == 0.537


def test_the_default_settings_are_the_first_preset():
    assert {s: P.SETTING_SPECS[s].default for s in P.SETTING_SPECS} == {"stacks_slider": 4, "height_slider": 4, "fill_slider": 60, "sigma_slider": 0.2, "bays_slider": 100, "seed_input": 0}
    assert C.PRESETS["Alltag (4 Stapel, Höhe 4, Schätzfehler 0,2)"] == {"stacks": 4, "height": 4, "fill": 60, "sigma": 0.2, "bays": 100, "seed": 0}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_apply_preset_writes_every_setting(name, monkeypatch):
    state = {}
    monkeypatch.setattr(P.st, "session_state", state)
    P.apply_preset(name)
    assert {k: state[sk] for k, sk in P.PRESET_KEYS.items()} == {k: C.PRESETS[name][k] for k in P.PRESET_KEYS}
    assert P.aktives_preset() == name
