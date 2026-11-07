"""Kern: Einlagern mit geschätzter Abfahrt, Umlagern beim Abruf und die Untergrenze der besten Ablage.

Container kommen nacheinander an; der i-te trägt die wahre Abfahrtsnummer arrivals[i] (1 = fährt als Erster ab, ein Rang, alle verschieden). Jeder wird beim Eintreffen sofort auf einen
Stapel mit Platz gesetzt (Höchsthöhe `height`) und bleibt dort, bis alle eingelagert sind. Danach werden die Container in der Reihenfolge der wahren Abfahrt abgerufen; liegt der
nächste nicht oben, werden die Container über ihm umgelagert (restricted: nur diese), jede Umlagerung kostet 1.

Einlege-Regeln (place):
  random   ein zufälliger Stapel mit Platz.
  lowest   der Stapel mit den wenigsten Containern (Gleichstand: kleinster Index): braucht keine Schätzung.
  tight    engste Passung nach der GESCHÄTZTEN Abfahrt (Stück 1 auf Schätzwerten): unter den Stapeln, deren frühester geschätzter Abfahrtswert später liegt als der des neuen Containers,
           der mit dem kleinsten solchen Wert (leerer Stapel = unendlich, zuletzt); gibt es keinen, der mit dem größten frühesten Wert. Schätzwert = wahre Nummer + sigma * N * z, z ~ N(0, 1).
           sigma = 0: volles Wissen.
Kosten beim Abruf: relocations (Regel engste Passung nach den WAHREN Nummern) und reloc_search (exaktes Optimum, IDA* mit Untergrenze).
Untergrenze der Ablage: min_blockers_storing = kleinste Blockerzahl der fertigen Bucht über alle möglichen Platzierungen; jede Umlagerung zählt mindestens einen Blocker, also gilt
Untergrenze <= Optimum beim Abruf <= Kosten der Regel.
"""

import random
from dataclasses import dataclass

INF = 10 ** 9
RULES = ("random", "lowest", "tight")


def make_arrivals(n: int, seed: int) -> list:
    """Wahre Abfahrtsnummern in der Reihenfolge der Ankunft: eine zufällige Permutation von 1 bis n, deterministisch aus (n, seed)."""
    rng = random.Random(seed)
    perm = list(range(1, n + 1))
    rng.shuffle(perm)
    return perm


def noise(n: int, seed: int) -> list:
    """Standardnormale Zufallszahlen z_i je Container (fest je Bucht: bei wachsendem sigma wächst der Fehler jedes Containers mit, gleiche Zufallszahlen)."""
    rng = random.Random(seed + 7_000_003)
    return [rng.gauss(0.0, 1.0) for _ in range(n)]


def estimates(arrivals, sigma: float, seed: int) -> list:
    """Geschätzte Abfahrtswerte: wahre Nummer + sigma * N * z."""
    n = len(arrivals)
    z = noise(n, seed)
    return [arrivals[i] + sigma * n * z[i] for i in range(n)]


def stack_blockers(stack) -> int:
    """Container in einem Stapel (unten nach oben), die über einem früher abzufahrenden liegen."""
    total, lowest = 0, INF
    for c in stack:
        if c > lowest:
            total += 1
        else:
            lowest = c
    return total


def blockers(bay) -> int:
    """Zahl der blockierenden Container einer Bucht (Untergrenze der Umlagerungen beim Abruf)."""
    return sum(stack_blockers(s) for s in bay)


def place(arrivals, stacks: int, height: int, rule: str, sigma: float = 0.0, seed: int = 0) -> tuple:
    """Legt die Ankömmlinge der Reihe nach ab und gibt die Bucht (Tupel von Stapeln mit WAHREN Nummern, von unten nach oben) zurück. Die Regel `tight` benutzt die Schätzwerte."""
    n = len(arrivals)
    if n > stacks * height:
        raise ValueError("mehr Container als Plätze")
    est = estimates(arrivals, sigma, seed)
    rng = random.Random(seed + 13)
    st = [[] for _ in range(stacks)]
    mins = [[] for _ in range(stacks)]            # geschätzte Werte je Stapel
    for i, r in enumerate(arrivals):
        room = [j for j in range(stacks) if len(st[j]) < height]
        if rule == "random":
            j = rng.choice(room)
        elif rule == "lowest":
            j = min(room, key=lambda k: (len(st[k]), k))
        elif rule == "tight":
            def key(k):
                m = min(mins[k]) if mins[k] else INF
                return (0, m, k) if m > est[i] else (1, -m, k)
            j = min(room, key=key)
        else:
            raise ValueError(f"unbekannte Regel {rule}")
        st[j].append(r)
        mins[j].append(est[i])
    return tuple(tuple(s) for s in st)


def relocations(bay, height: int) -> int:
    """Umlagerungen beim Abruf nach der Regel „engste Passung“ (wahre Nummern); wirft ValueError, wenn ein Blocker nirgends Platz findet."""
    st = [list(s) for s in bay]
    n = sum(len(s) for s in st)
    cost = 0
    for t in range(1, n + 1):
        k = next(i for i, s in enumerate(st) if t in s)
        while st[k][-1] != t:
            c = st[k].pop()
            room = [j for j in range(len(st)) if j != k and len(st[j]) < height]
            if not room:
                raise ValueError("kein Stapel mit Platz")

            def key(j):
                m = min(st[j]) if st[j] else INF
                return (0, m, j) if m > c else (1, -m, j)
            st[min(room, key=key)].append(c)
            cost += 1
        st[k].pop()
    return cost


def min_blockers_storing(arrivals, stacks: int, height: int) -> int:
    """Kleinste Blockerzahl der fertigen Bucht über alle Platzierungen der Ankömmlinge (Dynamik über kanonische Zustände, Stapel sortiert)."""
    states = {tuple(sorted([()] * stacks))}
    for r in arrivals:
        nxt = set()
        for st in states:
            seen = set()
            for j, s in enumerate(st):
                if len(s) >= height or s in seen:
                    continue
                seen.add(s)
                new = list(st)
                new[j] = s + (r,)
                nxt.add(tuple(sorted(new)))
        states = nxt
    return min(blockers(s) for s in states)


# ---------------------------------------------------------------- exaktes Optimum beim Abruf (Stück 5 bis 9, verschlankt)

def autopop(stacks):
    """Ruft ab, was oben liegt und gerade dran ist. Gibt (neue Stapel, abgerufene Nummern in Reihenfolge) zurück."""
    st = [list(s) for s in stacks]
    popped = []
    while True:
        present = [c for s in st for c in s]
        if not present:
            return tuple(tuple(s) for s in st), popped
        t = min(present)
        for s in st:
            if s and s[-1] == t:
                s.pop()
                popped.append(t)
                break
        else:
            return tuple(tuple(s) for s in st), popped


def _target_stack(stacks):
    t = min(c for s in stacks for c in s)
    for i, s in enumerate(stacks):
        if t in s:
            return t, i


def _stack_min(stack):
    return min(stack) if stack else INF


def reloc_lb(stacks) -> int:
    """Untergrenze des Relocation (Stück 9, LB2): Blocker plus Blocker über dem Ziel ohne sicheren Stapel."""
    if not any(stacks):
        return 0
    t, i = _target_stack(stacks)
    s = stacks[i]
    above = s[s.index(t) + 1:]
    others = [_stack_min(x) for k, x in enumerate(stacks) if k != i]
    top = max(others) if others else -1
    return blockers(stacks) + sum(1 for c in above if c > top)


def _child_targets(stacks, src, height, c):
    dests = [j for j in range(len(stacks)) if j != src and len(stacks[j]) < height]

    def fit(j):
        m = _stack_min(stacks[j])
        return (0, m) if m > c else (1, -m)
    dests.sort(key=lambda j: (fit(j), j))
    return dests


@dataclass(frozen=True)
class RelocResult:
    optimum: int | None     # None bei Knotenlimit
    nodes: int
    capped: bool


class _Cap(Exception):
    pass


class _Found(Exception):
    pass


def reloc_search(bay, height: int, cap: int = 100_000) -> RelocResult:
    """Exaktes Optimum der Umlagerungen beim Abruf: IDA* mit Untergrenze und Zustandsmerken (kanonisch)."""
    start = tuple(tuple(s) for s in bay)
    budget = reloc_lb(autopop(start)[0])
    total = 0
    while True:
        b = budget
        nodes = [0]
        table = {}
        found = []

        def rec(state, g):
            nodes[0] += 1
            if total + nodes[0] > cap:
                raise _Cap
            st, _ = autopop(state)
            if not any(st):
                found.append(g)
                raise _Found
            if g + reloc_lb(st) > b:
                return
            key = tuple(sorted(st))
            if table.get(key, INF) <= g:
                return
            table[key] = g
            _, i = _target_stack(st)
            lst = [list(s) for s in st]
            c = lst[i].pop()
            base = tuple(tuple(s) for s in lst)
            for j in _child_targets(base, i, height, c):
                nxt = [list(s) for s in lst]
                nxt[j].append(c)
                rec(tuple(tuple(s) for s in nxt), g + 1)

        try:
            rec(start, 0)
        except _Found:
            pass
        except _Cap:
            return RelocResult(None, cap, True)
        total += nodes[0]
        if found:
            return RelocResult(found[0], total, False)
        budget += 1
