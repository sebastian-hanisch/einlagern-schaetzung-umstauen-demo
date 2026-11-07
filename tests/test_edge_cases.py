"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import pytest

import eas_algorithm as A
import eas_constants as C
import eas_evaluation as ev
import eas_presets as P


def test_container_count_rounds_half_up_and_clamps():
    assert ev.container_count(3, 4, 65) == 8 and ev.container_count(4, 4, 60) == 10 and ev.container_count(6, 4, 75) == 18          # 12 · 0,65 = 7,8; 16 · 0,6 = 9,6; 24 · 0,75 = 18
    assert ev.container_count(3, 3, 80) == 6                                              # 7,2 gerundet 7, aber höchstens Plätze − Höchsthöhe = 6: ein Blocker findet immer Platz
    assert ev.container_count(3, 3, 30) == 3 and ev.container_count(3, 3, 5) == 2          # mindestens 2
    assert ev.container_count(3, 4, 62.5) == 8 and ev.container_count(3, 4, 54) == 6        # 7,5 rundet auf 8; 6,48 auf 6


def test_a_bay_never_needs_more_room_than_it_has():
    for s in (3, 4, 5, 6):
        for h in (3, 4, 5):
            for f in (30, 55, 80):
                n = ev.container_count(s, h, f)
                assert 2 <= n <= s * h - h
                bay = A.place(A.make_arrivals(n, 0), s, h, "tight", 4.0, 0)
                assert A.relocations(bay, h) >= 0                                          # beim Abruf findet jeder Blocker einen Stapel mit Platz (kein ValueError)


def test_closed_share_by_hand_and_without_a_gap():
    assert ev.closed_share(4.0, 2.0, 1.0) == pytest.approx(2 / 3) and ev.closed_share(4.0, 1.0, 1.0) == 1.0 and ev.closed_share(4.0, 4.0, 1.0) == 0.0
    assert ev.closed_share(4.0, 4.3, 1.0) == pytest.approx(-0.1)                           # schlechter als der niedrigste Stapel: negativ
    assert ev.closed_share(1.0, 0.5, 1.0) is None and ev.closed_share(0.5, 0.5, 1.0) is None     # volles Wissen nicht besser: keine Lücke


def _row(seed, random, lowest, tight, full, blockers=1, lb=None, exact=None):
    return {"seed": seed, "random": random, "lowest": lowest, "tight": tight, "full": full, "blockers": blockers, "lb": lb, "exact": exact}


def test_sample_stats_by_hand_without_and_with_the_bounds():
    rows = [_row(0, 5, 4, 2, 1), _row(1, 4, 4, 3, 0), _row(2, 6, 5, 2, 1)]
    s = ev.sample_stats(rows)
    assert s["n"] == 3 and s["random"] == 5 and s["lowest"] == pytest.approx(13 / 3) and s["tight"] == pytest.approx(7 / 3) and s["full"] == pytest.approx(2 / 3) and "lb" not in s and "exact" not in s
    assert s["closed"] == pytest.approx((13 / 3 - 7 / 3) / (13 / 3 - 2 / 3))
    rows = [_row(0, 5, 4, 2, 1, lb=1, exact=2), _row(1, 4, 4, 3, 0, lb=0, exact=3), _row(2, 6, 5, 2, 1, lb=1, exact=None)]
    s = ev.sample_stats(rows)
    assert s["lb"] == pytest.approx(2 / 3) and s["lb_violations"] == 0 and s["exact"] == 2.5 and s["exact_n"] == 2 and s["exact_violations"] == 0


def test_violations_of_the_chain_are_counted():
    s = ev.sample_stats([_row(0, 5, 4, 2, 1, lb=2, exact=1)])                              # Untergrenze über der Regel mit vollem Wissen, exaktes Optimum unter der Untergrenze
    assert s["lb_violations"] == 1 and s["exact_violations"] == 1
    assert ev.sample_stats([_row(0, 5, 4, 2, 1, lb=0, exact=3)])["exact_violations"] == 1  # exaktes Optimum über der Regel


def test_sigma_stats_and_the_kipp_point_on_given_rows():
    sig = (0.0, 1.0, 2.0)
    rows = [{"seed": 0, "random": 6, "lowest": 5, "tight": {"0": 1, "1": 4, "2": 6}}, {"seed": 1, "random": 4, "lowest": 3, "tight": {"0": 1, "1": 2, "2": 3}}]
    s = ev.sigma_stats(rows, sig)
    assert s["n"] == 2 and s["random"] == 5 and s["lowest"] == 4 and s["tight"] == {"0": 1.0, "1": 3.0, "2": 4.5}
    assert s["closed"] == {"0": 1.0, "1": pytest.approx(1 / 3), "2": pytest.approx(-1 / 6)} and s["kipp"] == 2.0                  # bei σ = 2 kostet die Schätzung 4,5 ≥ 4
    rows[0]["tight"]["2"], rows[1]["tight"]["2"] = 4, 3                                      # Mittel 3,5 < 4: kein Kipppunkt
    assert ev.sigma_stats(rows, sig)["kipp"] is None
    rows[0]["tight"]["2"], rows[1]["tight"]["2"] = 5, 3                                      # Mittel genau 4: gleich teuer zählt als Kipppunkt
    assert ev.sigma_stats(rows, sig)["kipp"] == 2.0


def test_lb_stats_on_given_rows_and_the_violation_count():
    sig = (0.0, 1.0)
    rows = [{"seed": 0, "lb": 1, "random": 5, "lowest": 4, "greedy": {"0": 1, "1": 3}, "exact": {"0": 1, "1": 3}}, {"seed": 1, "lb": 0, "random": 3, "lowest": 4, "greedy": {"0": 0, "1": 2}, "exact": {"0": 0, "1": 1}}]
    s = ev.lb_stats(rows, sig)
    assert s["lb"] == 0.5 and s["lowest"] == 4 and s["random"] == 4 and s["greedy"] == {"0": 0.5, "1": 2.5} and s["exact"] == {"0": 0.5, "1": 2.0} and s["violations"] == 0
    rows[1]["exact"]["1"] = None                                                              # kein Optimum (Limit): zählt als Verletzung der Prüfkette
    s = ev.lb_stats(rows, sig)
    assert s["violations"] == 1 and s["exact"]["1"] == 3.0 and s["exact"]["0"] == 0.5


def test_number_and_sigma_formats():
    assert ev.num(5) == "5" and ev.num(60234) == "60 234"
    assert ev.dec(5.0) == "5" and ev.dec(0.485) == "0,49" and ev.dec(0.615) == "0,62" and ev.dec(4.999999999) == "5" and ev.dec(1234.5) == "1 234,50"
    assert ev.percent_text(0.555) == "56 %" and ev.percent_text(-0.086) == "-9 %" and ev.percent_text(1.0) == "100 %" and ev.percent_text(0.625) == "63 %"
    assert ev.sigma_text(0.05) == "0,05" and ev.sigma_text(0.0) == "0" and ev.sigma_text(4.0) == "4" and ev.sigma_text(0.75) == "0,75"
    assert ev.sigma_key(0.05) == "0.05" and ev.sigma_key(1.0) == "1" and ev.key(4, 4, 10) == "4,4,10"


def test_the_settings_snap_to_the_steps():
    assert P.snap("sigma_slider", 0.07) == 0.05 and P.snap("sigma_slider", 0.15) == 0.1 and P.snap("sigma_slider", 9.0) == 4.0 and P.snap("sigma_slider", -1.0) == 0.0
    assert P.snap("fill_slider", 62) == 60 and P.snap("fill_slider", 63) == 65 and P.snap("fill_slider", 10) == 30 and P.snap("fill_slider", 99) == 80
    assert P.snap("bays_slider", 80) == 100 and P.snap("stacks_slider", 9) == 6 and P.snap("seed_input", -3) == 0
