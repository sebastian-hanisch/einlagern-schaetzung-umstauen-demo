"""Orakel-Test einlagern-schaetzung-umstauen-demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12): Ablage, Abruf und Untergrenze gegen ANDERE Rechenwege.

Eigene, unabhängige Umsetzungen im Test: (a) die Untergrenze der besten Ablage durch Aufzählen aller Platzierungen (itertools.product über die Stapelwahl je Container, ohne Zustandsmengen),
(b) die Regel „engste Passung“ beim Einlegen mit ausgeschriebenen Schleifen statt Schlüsselfunktion, (c) der Abruf durch vollständige Rekursion über alle Umlagerungen (ohne Untergrenze, ohne IDA*),
(d) die Blockerzahl durch Paarvergleich. Vorher an den Handzahlen geprüft: Bucht (1, 3), (2): 2 Umlagerungen, Bucht (1), (2, 3): 1, Untergrenze 1."""

import functools
import itertools

import pytest

import eas_algorithm as A
import eas_evaluation as ev

INF = 10 ** 9


def ref_blockers(bay):
    """Blockerzahl durch Paarvergleich: ein Container ist ein Blocker, wenn irgendwo unter ihm im selben Stapel eine kleinere Nummer liegt."""
    return sum(1 for s in bay for i, c in enumerate(s) if any(s[j] < c for j in range(i)))


def ref_min_blockers(arrivals, stacks, height):
    best = INF
    for choice in itertools.product(range(stacks), repeat=len(arrivals)):
        st = [[] for _ in range(stacks)]
        ok = True
        for c, j in zip(arrivals, choice):
            if len(st[j]) >= height:
                ok = False
                break
            st[j].append(c)
        if ok:
            best = min(best, ref_blockers(st))
    return best


def ref_tight(arrivals, stacks, height, est):
    """Engste Passung nach Schätzwerten, ausgeschrieben: sichere Stapel (frühester Wert später als der des Neuen) nach kleinstem frühestem Wert, leer = unendlich; sonst größter früher Wert."""
    st = [[] for _ in range(stacks)]
    vals = [[] for _ in range(stacks)]
    for i, r in enumerate(arrivals):
        best, best_key = None, None
        for k in range(stacks):
            if len(st[k]) >= height:
                continue
            m = min(vals[k]) if vals[k] else float("inf")
            if m > est[i]:
                cand = (0, m, k)
            else:
                cand = (1, -m, k)
            if best_key is None or cand < best_key:
                best, best_key = k, cand
        st[best].append(r)
        vals[best].append(est[i])
    return tuple(tuple(s) for s in st)


def ref_reloc(bay, height):
    @functools.lru_cache(maxsize=None)
    def rec(state):
        st = [list(s) for s in state]
        while True:
            nums = [c for s in st for c in s]
            if not nums:
                return 0
            t = min(nums)
            k = next(i for i, s in enumerate(st) if t in s)
            if st[k][-1] != t:
                break
            st[k].pop()
        best = INF
        for j in range(len(st)):
            if j != k and len(st[j]) < height:
                new = [list(s) for s in st]
                new[j].append(new[k].pop())
                best = min(best, 1 + rec(tuple(sorted(tuple(s) for s in new))))
        return best
    return rec(tuple(sorted(tuple(s) for s in bay)))


def test_blockers_equal_the_pairwise_count():
    for sd in range(40):
        bay = A.place(A.make_arrivals(9, sd), 3, 4, "random", 0.0, sd)
        assert A.blockers(bay) == ref_blockers(bay)


@pytest.mark.parametrize("stacks,height,n", [(2, 3, 4), (3, 3, 6), (3, 2, 5), (2, 4, 6), (3, 3, 7)])
def test_the_lower_bound_equals_the_enumeration_of_all_placements(stacks, height, n):
    for sd in range(25):
        arr = A.make_arrivals(n, sd)
        assert A.min_blockers_storing(arr, stacks, height) == ref_min_blockers(arr, stacks, height), (stacks, height, n, sd)


def test_the_tight_rule_equals_the_written_out_version_for_every_sigma():
    for stacks, height, n in ((3, 4, 8), (4, 4, 10), (6, 4, 18)):
        for sd in range(30):
            arr = A.make_arrivals(n, sd)
            for sg in (0.0, 0.1, 0.5, 2.0):
                assert A.place(arr, stacks, height, "tight", sg, sd) == ref_tight(arr, stacks, height, A.estimates(arr, sg, sd)), (stacks, height, n, sd, sg)


def test_the_exact_optimum_equals_the_independent_recursion_and_the_chain_of_bounds_holds():
    n = 0
    for stacks, height, count in ((3, 4, 8), (4, 3, 7), (3, 3, 6)):
        for sd in range(30):
            arr = A.make_arrivals(count, sd)
            lb = A.min_blockers_storing(arr, stacks, height)
            for rule, sg in (("lowest", 0.0), ("random", 0.0), ("tight", 0.0), ("tight", 0.3), ("tight", 2.0)):
                bay = A.place(arr, stacks, height, rule, sg, sd)
                exact = A.reloc_search(bay, height, 200_000).optimum
                assert exact == ref_reloc(bay, height), (stacks, height, count, sd, rule, sg)
                assert lb <= A.blockers(bay) <= exact <= A.relocations(bay, height)            # Untergrenze der Ablage ≤ Blocker ≤ exaktes Optimum ≤ Regel beim Abruf
                n += 1
    assert n == 450


def test_the_row_statistics_satisfy_the_chain_on_a_sample():
    rows = [ev.bay_row(3, 4, 8, sd, 0.2, True, True) for sd in range(40)]
    for r in rows:
        assert r["lb"] <= min(r["random"], r["lowest"], r["tight"], r["full"]) and r["lb"] <= r["exact"] <= r["tight"]
    s = ev.sample_stats(rows)
    assert s["lb_violations"] == 0 and s["exact_violations"] == 0 and s["exact_n"] == 40


def test_full_knowledge_is_never_worse_than_no_knowledge_on_average_and_the_error_makes_it_worse():
    """Eigenschaft über feste Buchten: im Mittel gilt volles Wissen ≤ kleiner Fehler ≤ großer Fehler (Kernmessung in klein, 150 Buchten)."""
    means = {}
    for sg in (0.0, 0.2, 1.0, 4.0):
        means[sg] = sum(A.relocations(A.place(A.make_arrivals(10, sd), 4, 4, "tight", sg, sd), 4) for sd in range(150)) / 150
    assert means[0.0] < means[0.2] < means[1.0] < means[4.0]
    low = sum(A.relocations(A.place(A.make_arrivals(10, sd), 4, 4, "lowest"), 4) for sd in range(150)) / 150
    assert means[0.2] < low < means[4.0]                                                     # bei σ = 4 ist die Schätzung schlechter als der niedrigste Stapel
