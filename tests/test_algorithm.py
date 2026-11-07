"""Einlegen, Abruf und Untergrenze gegen Handrechnung (DEMO-PLAYBOOK §1b und §12)."""

import pytest

import eas_algorithm as A


def test_arrivals_and_noise_are_deterministic_permutations():
    arr = A.make_arrivals(8, 0)
    assert arr == [5, 2, 6, 3, 1, 4, 8, 7] and sorted(arr) == list(range(1, 9)) and A.make_arrivals(8, 0) == arr and A.make_arrivals(8, 1) != arr
    z = A.noise(3, 0)
    assert [round(x, 3) for x in z] == [-1.56, -1.445, 1.84] and A.noise(3, 0) == z and len(A.noise(5, 0)) == 5
    assert A.noise(3, 0) == A.noise(5, 0)[:3]                                           # gleiche Zufallszahlen: bei größerem N bleiben die ersten gleich


def test_estimates_scale_with_sigma_and_container_count():
    arr = [1, 2, 3]
    assert A.estimates(arr, 0.0, 0) == [1.0, 2.0, 3.0]
    est = A.estimates(arr, 0.5, 0)                                                      # Fehler = sigma * N * z mit N = 3
    z = A.noise(3, 0)
    assert est == pytest.approx([arr[i] + 0.5 * 3 * z[i] for i in range(3)])
    assert A.estimates(arr, 1.0, 0)[0] - 1 == pytest.approx(2 * (A.estimates(arr, 0.5, 0)[0] - 1))      # gleiches z: der Fehler wächst linear mit sigma


def test_blockers_by_hand():
    assert A.stack_blockers((1, 3)) == 1 and A.stack_blockers((3, 1)) == 0 and A.stack_blockers((2, 3, 1, 4)) == 2 and A.stack_blockers(()) == 0
    assert A.blockers(((1, 3), (2,))) == 1 and A.blockers(((2, 1), (3,))) == 0


def test_placement_rules_by_hand(ascending, sortable):
    arr, s, h = ascending
    assert A.place(arr, s, h, "lowest") == ((1, 3), (2,))
    assert A.place(arr, s, h, "tight", 0.0, 0) == ((1,), (2, 3))
    arr, s, h = sortable
    assert A.place(arr, s, h, "tight", 0.0, 0) == ((2, 1), (3,)) and A.place(arr, s, h, "lowest") == ((2, 1), (3,))


def test_random_rule_is_deterministic_and_respects_room():
    arr = A.make_arrivals(9, 3)
    a = A.place(arr, 3, 3, "random", 0.0, 3)
    assert a == A.place(arr, 3, 3, "random", 0.0, 3) and all(len(x) <= 3 for x in a) and sorted(c for x in a for c in x) == list(range(1, 10))
    assert A.place(arr, 3, 3, "random", 0.0, 4) != a or A.place(arr, 3, 3, "random", 0.0, 5) != a      # eine andere Bucht-Nummer gibt (fast immer) eine andere Ablage


def test_lowest_rule_fills_evenly():
    assert [len(x) for x in A.place(list(range(1, 11)), 4, 4, "lowest")] == [3, 3, 2, 2]


def test_place_rejects_too_many_containers_and_unknown_rules():
    with pytest.raises(ValueError):
        A.place([1, 2, 3, 4, 5], 2, 2, "lowest")
    with pytest.raises(ValueError):
        A.place([1, 2], 2, 2, "gewuerfelt")


def test_relocations_by_hand(ascending, sortable):
    arr, s, h = ascending
    assert A.relocations(A.place(arr, s, h, "lowest"), h) == 2 and A.relocations(A.place(arr, s, h, "tight", 0.0, 0), h) == 1
    arr, s, h = sortable
    assert A.relocations(A.place(arr, s, h, "tight", 0.0, 0), h) == 0
    assert A.relocations(((1, 3, 2), (), ()), 3) == 2                                      # die 2 und die 3 liegen über der 1; beide werden einzeln umgelagert (2 zuerst, auf einen leeren Stapel)


def test_relocations_refuse_a_bay_without_room():
    with pytest.raises(ValueError):
        A.relocations(((1, 2), (3, 4)), 2)                                                 # beide Stapel voll: die 2 findet keinen Platz


def test_min_blockers_storing_by_hand(ascending, sortable):
    assert A.min_blockers_storing(*ascending) == 1 and A.min_blockers_storing(*sortable) == 0
    assert A.min_blockers_storing([3, 2, 1], 1, 3) == 0 and A.min_blockers_storing([1, 2, 3], 1, 3) == 2        # ein Stapel: absteigend ankommend sortiert; aufsteigend liegen 2 und 3 über der 1


def test_exact_relocation_optimum_by_hand():
    assert A.reloc_search(((1, 3), (2,)), 3).optimum == 2 and A.reloc_search(((1,), (2, 3)), 3).optimum == 1
    assert A.reloc_search(((2, 1), (3,)), 3).optimum == 0
    r = A.reloc_search(((1, 2), (3, 4)), 2, cap=30)
    assert r.optimum is None and r.capped and r.nodes == 30                                # ohne Platz läuft die Suche bis zum Limit
    assert A.reloc_lb(((1, 5), (2, 3), (4, 6))) == 4 and A.reloc_lb(()) == 0
