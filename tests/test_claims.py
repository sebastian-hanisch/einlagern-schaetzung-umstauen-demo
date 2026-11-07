"""Aussagen der Demo und des READMEs gegen die vorberechneten Bänder und gegen eine frische Nachrechnung kleiner Zellen (DEMO-PLAYBOOK §5, §12).

Alle Größen sind deterministisch (feste Seeds, Rauschen aus random.Random(seed), keine Zeiten) und müssen bei der Nachrechnung gleich sein."""

import pytest

import eas_constants as C
import eas_evaluation as ev


def K(s, h, n):
    return ev.key(s, h, n)


def _bands():
    return ev.load_bands()


def test_the_stored_cells_cover_exactly_the_cells_of_the_constants():
    b = _bands()
    assert set(b["sigma"]) == {K(*c) for c in C.SIGMA_CELLS} and all(c["n"] == C.SIGMA_BAYS for c in b["sigma"].values())
    assert set(b["lb"]) == {K(*c) for c in C.LB_CELLS} and all(c["n"] == C.LB_BAYS for c in b["lb"].values())


def test_the_cost_rises_with_the_estimation_error_in_every_cell():
    for c in _bands()["sigma"].values():
        costs = [c["tight"][ev.sigma_key(x)] for x in C.SIGMA_OPTIONS]
        assert all(a < b for a, b in zip(costs, costs[1:])), costs                            # streng monoton über alle 12 Stufen
        assert c["lowest"] < c["random"] and c["closed"]["0"] == 1.0


def test_the_closed_share_the_readme_quotes():
    sig = _bands()["sigma"]
    at02 = [sig[K(*c)]["closed"]["0.2"] for c in C.SIGMA_CELLS]
    assert [round(x, 2) for x in at02] == [0.63, 0.58, 0.56, 0.58, 0.54, 0.56] and round(min(at02), 2) == 0.54 and round(max(at02), 2) == 0.63
    at01 = [sig[K(*c)]["closed"]["0.1"] for c in C.SIGMA_CELLS]
    assert [round(x, 2) for x in at01] == [0.83, 0.81, 0.81, 0.78, 0.75, 0.79]
    at005 = [round(sig[K(*c)]["closed"]["0.05"], 2) for c in C.SIGMA_CELLS]
    assert min(at005) == 0.90 and max(at005) == 0.96
    at2 = [sig[K(*c)]["closed"]["2"] for c in C.SIGMA_CELLS]
    assert max(at2) < 0.09 and min(at2) >= 0.0


def test_the_kipp_points_the_readme_quotes():
    sig = _bands()["sigma"]
    assert sig[K(3, 4, 8)]["kipp"] is None and all(sig[K(*c)]["kipp"] == 3.0 for c in C.SIGMA_CELLS if c != (3, 4, 8))
    assert sig[K(3, 4, 8)]["tight"]["4"] < sig[K(3, 4, 8)]["lowest"] and sig[K(4, 4, 10)]["tight"]["3"] >= sig[K(4, 4, 10)]["lowest"] > sig[K(4, 4, 10)]["tight"]["2"] - 0.1
    assert all(sig[K(*c)]["closed"]["3"] < 0.05 for c in C.SIGMA_CELLS) and sum(1 for c in C.SIGMA_CELLS if sig[K(*c)]["closed"]["3"] < 0) == 5        # bei σ = 3 ist die Schätzung in fünf von sechs Zellen schlechter als der niedrigste Stapel


def test_the_costs_the_readme_quotes():
    sig = _bands()["sigma"]
    assert [round(sig[K(*c)]["tight"]["0"], 2) for c in C.SIGMA_CELLS] == [1.16, 0.58, 1.44, 0.73, 0.99, 2.43]
    assert [round(sig[K(*c)]["lowest"], 2) for c in C.SIGMA_CELLS] == [4.05, 4.11, 6.14, 6.23, 8.44, 8.42] and [round(sig[K(*c)]["random"], 2) for c in C.SIGMA_CELLS] == [4.21, 4.49, 6.7, 6.64, 8.91, 9.09]


def test_the_lower_bound_numbers_the_readme_quotes():
    lb = _bands()["lb"]
    small, mid = lb[K(3, 4, 8)], lb[K(4, 4, 10)]
    assert (round(small["lb"], 2), round(mid["lb"], 2)) == (0.90, 0.49) and (round(small["greedy"]["0"], 2), round(mid["greedy"]["0"], 2)) == (1.23, 0.61)
    assert (round(small["lowest"], 2), round(mid["lowest"], 2)) == (4.08, 4.05) and ev.dec(small["greedy"]["0"] - small["lb"]) == "0,34" and ev.dec(mid["greedy"]["0"] - mid["lb"]) == "0,12"
    assert ev.dec(small["lowest"] - small["lb"]) == "3,18" and ev.dec(mid["lowest"] - mid["lb"]) == "3,56"
    assert small["violations"] == 0 and mid["violations"] == 0                                # 2 Zellen · 200 Buchten · 8 Stufen = 3 200 Paare ohne Verletzung von Untergrenze ≤ exakt ≤ Regel
    for c in (small, mid):
        assert all(c["exact"][k] <= c["greedy"][k] + 1e-9 and c["greedy"][k] - c["exact"][k] < 0.1 for k in c["greedy"])


@pytest.mark.parametrize("cell", [(3, 4, 8)])
def test_a_fresh_recomputation_of_a_sigma_cell_reproduces_the_stored_band(cell):
    stored = _bands()["sigma"][K(*cell)]
    fresh = ev.sigma_stats(ev.sigma_rows(*cell, range(C.SIGMA_BAYS)))
    assert fresh == stored


def test_a_fresh_recomputation_of_a_lower_bound_cell_reproduces_the_stored_band():
    stored = _bands()["lb"][K(3, 4, 8)]
    assert ev.lb_stats(ev.lb_rows(3, 4, 8, range(C.LB_BAYS))) == stored
