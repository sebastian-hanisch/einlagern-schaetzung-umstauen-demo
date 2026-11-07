"""Abbildungen an synthetischen Daten: Werte, Farben, gesperrte Achsen (DEMO-PLAYBOOK §12)."""

import plotly.graph_objects as go
import pytest

import eas_constants as C
import eas_evaluation as ev
import eas_visualization as V


def _locked(fig):
    return fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True


def test_blocker_cells_by_hand():
    assert V.blocker_cells(((1, 3), (2,))) == {(0, 1)} and V.blocker_cells(((2, 1), (3,))) == set()


def test_bay_chart_with_free_slots_colours_and_height_line():
    fig = V.build_bay(((1, 3), (2,), ()), 4)
    assert _locked(fig) and len(fig.data) == 4 and list(fig.layout.yaxis.range) == [0, 4.35]
    assert list(fig.data[0].marker.color) == [C.COLOR_CELL] * 3 and list(fig.data[0].text) == ["1", "2", ""] and list(fig.data[0].y) == [1, 1, 0]
    assert list(fig.data[1].marker.color)[0] == C.COLOR_BLOCK and list(fig.data[1].y) == [1, 0, 0] and [s.y0 for s in fig.layout.shapes] == [4]


def _sig_cells():
    cells = {}
    for i, k in enumerate(("4,4,10", "3,4,8")):
        cells[k] = {"closed": {ev.sigma_key(x): 1.0 - x / 4 for x in C.SIGMA_OPTIONS}}
    return cells


def test_closed_chart_has_one_line_per_cell_in_percent():
    fig = V.build_closed(_sig_cells())
    assert _locked(fig) and [t.name for t in fig.data] == ["3 Stapel, Höhe 4, 8 Container", "4 Stapel, Höhe 4, 10 Container"]
    assert list(fig.data[0].x) == ["0", "0,05", "0,1", "0,2", "0,3", "0,5", "0,75", "1", "1,5", "2", "3", "4"] and list(fig.data[0].y)[:3] == pytest.approx([100.0, 98.75, 97.5])
    assert fig.layout.xaxis.type == "category" and not fig.layout.shapes


def _lb():
    return {"lb": 0.49, "lowest": 4.05, "random": 4.62, "greedy": {ev.sigma_key(x): 0.6 + x for x in C.LB_SIGMAS}, "exact": {ev.sigma_key(x): 0.55 + x for x in C.LB_SIGMAS}}


def test_cost_chart_has_the_two_curves_and_three_reference_lines():
    fig = V.build_cost(_lb())
    assert _locked(fig) and not fig.layout.shapes and len(fig.data) == 5 and fig.layout.yaxis.rangemode == "tozero"
    assert [t.name for t in fig.data] == ["engste Passung nach Schätzung", "exaktes Optimum nach der Ablage", "niedrigster Stapel", "zufälliger Stapel", "Untergrenze der besten Ablage"]
    assert list(fig.data[0].y)[0] == pytest.approx(0.6) and list(fig.data[1].y)[-1] == pytest.approx(4.55) and set(fig.data[2].y) == {4.05} and set(fig.data[4].y) == {0.49}
    assert list(fig.data[0].x) == ["0", "0,1", "0,2", "0,5", "1", "2", "3", "4"]


def test_rules_chart_with_and_without_the_lower_bound():
    s = {"lowest": 4.0, "random": 4.5, "tight": 2.0, "full": 1.0}
    fig = V.build_rules(s)
    assert _locked(fig) and list(fig.data[0].x) == ["volles Wissen", "mit Schätzung", "niedrigster Stapel", "zufälliger Stapel"] and list(fig.data[0].y) == [1.0, 2.0, 4.0, 4.5]
    fig = V.build_rules({**s, "lb": 0.49})
    assert list(fig.data[0].x)[0] == "Untergrenze" and list(fig.data[0].y)[0] == 0.49 and fig.data[0].marker.color[0] == C.COLOR_LB and list(fig.data[0].text)[0] == "0,49"


def test_all_figures_are_plotly_figures():
    assert all(isinstance(f, go.Figure) for f in (V.build_bay(((1,),), 2), V.build_closed(_sig_cells()), V.build_cost(_lb())))
