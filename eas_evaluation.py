"""Kennzahlen, Verdikt-Logik, vorberechnete Tabellen. Reine Funktionen: die App ruft st.<Art>(Text), die Tests prüfen jede Zahl und jede Schwelle."""

import json
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from statistics import mean

import eas_algorithm as A
import eas_constants as C

BANDS_FILE = Path(__file__).resolve().parent / "eas_bands.json"
RULE_NAMES = {"random": "zufälliger Stapel", "lowest": "niedrigster Stapel", "tight": "engste Passung nach Schätzung", "full": "engste Passung mit vollem Wissen"}


@dataclass(frozen=True)
class Settings:
    stacks: int = C.DEFAULT_STACKS
    height: int = C.DEFAULT_HEIGHT
    fill: int = C.DEFAULT_FILL
    sigma: float = C.DEFAULT_SIGMA
    bays: int = C.DEFAULT_BAYS
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    n: int                  # Container je Bucht
    height: int
    rows: tuple             # je Bucht {"seed", "random", "lowest", "tight", "full", "lb" (oder None), "exact" (oder None)}
    stats: dict             # sample_stats
    example: dict           # die erste Bucht: {"arrivals", "estimates", "bays": {"random", "lowest", "tight", "full"}}


def container_count(stacks: int, height: int, fill: int) -> int:
    """Container bei `fill` Prozent Füllgrad (kaufmännisch gerundet); höchstens Plätze − Höchsthöhe (so bleibt beim Abruf immer Platz für einen Blocker), mindestens 2."""
    n = int((Decimal(fill) * stacks * height / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return max(2, min(n, stacks * height - height))


def bay_row(stacks: int, height: int, n: int, seed: int, sigma: float, with_lb: bool = False, with_exact: bool = False) -> dict:
    """Eine Bucht: Umlagerungen beim Abruf (Regel engste Passung) nach jeder Einlege-Regel, dazu optional Untergrenze der Ablage und exaktes Optimum nach `tight`."""
    arr = A.make_arrivals(n, seed)
    random_bay = A.place(arr, stacks, height, "random", 0.0, seed)
    lowest_bay = A.place(arr, stacks, height, "lowest", 0.0, seed)
    tight_bay = A.place(arr, stacks, height, "tight", sigma, seed)
    full_bay = A.place(arr, stacks, height, "tight", 0.0, seed)
    return {"seed": seed, "random": A.relocations(random_bay, height), "lowest": A.relocations(lowest_bay, height), "tight": A.relocations(tight_bay, height),
            "full": A.relocations(full_bay, height), "blockers": A.blockers(tight_bay),
            "lb": A.min_blockers_storing(arr, stacks, height) if with_lb else None,
            "exact": A.reloc_search(tight_bay, height, C.EXACT_CAP).optimum if with_exact else None}


def closed_share(lowest: float, tight: float, full: float):
    """Anteil der Lücke zwischen „niedrigster Stapel“ und vollem Wissen, den die Schätzung schließt; None, wenn es keine Lücke gibt."""
    if lowest - full <= 0:
        return None
    return (lowest - tight) / (lowest - full)


def sample_stats(rows: list[dict]) -> dict:
    """Mittel der Umlagerungen je Regel, Anteil der geschlossenen Lücke, mittlere Blockerzahl der Bucht nach Schätzung; mit Untergrenze und exaktem Optimum die entsprechenden Mittel."""
    out = {"n": len(rows)}
    for k in ("random", "lowest", "tight", "full", "blockers"):
        out[k] = mean(r[k] for r in rows)
    out["closed"] = closed_share(out["lowest"], out["tight"], out["full"])
    lbs = [r for r in rows if r["lb"] is not None]
    if lbs:
        out["lb"] = mean(r["lb"] for r in lbs)
        out["lb_violations"] = sum(1 for r in lbs if any(r["lb"] > r[k] for k in ("random", "lowest", "tight", "full")))
    ex = [r for r in rows if r["exact"] is not None]
    if ex:
        out["exact"] = mean(r["exact"] for r in ex)
        out["exact_n"] = len(ex)
        out["exact_violations"] = sum(1 for r in ex if r["exact"] > r["tight"] or (r["lb"] is not None and r["lb"] > r["exact"]))
    return out


def analyse(settings: Settings) -> Analysis:
    n = container_count(settings.stacks, settings.height, settings.fill)
    with_lb = n <= C.LB_MAX_CONTAINERS
    with_exact = n <= C.EXACT_MAX_CONTAINERS
    rows = [bay_row(settings.stacks, settings.height, n, sd, settings.sigma, with_lb, with_exact) for sd in range(settings.seed, settings.seed + settings.bays)]
    arr = A.make_arrivals(n, settings.seed)
    example = {"arrivals": arr, "estimates": A.estimates(arr, settings.sigma, settings.seed),
               "bays": {"random": A.place(arr, settings.stacks, settings.height, "random", 0.0, settings.seed), "lowest": A.place(arr, settings.stacks, settings.height, "lowest", 0.0, settings.seed),
                        "tight": A.place(arr, settings.stacks, settings.height, "tight", settings.sigma, settings.seed), "full": A.place(arr, settings.stacks, settings.height, "tight", 0.0, settings.seed)}}
    return Analysis(n, settings.height, tuple(rows), sample_stats(rows), example)


# ---------------------------------------------------------------- Formate

def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def _half_up(x: float, digits: int) -> str:
    """Kaufmännisch gerundet (…5 rundet auf) mit `digits` Nachkommastellen (vermeidet die Binärdarstellung: 1,635 als 1,63)."""
    d = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    return f"{d:.{digits}f}"


def dec(x: float, digits: int = 2) -> str:
    """Dezimalzahl mit Komma und Leerzeichen als Tausendertrenner; ganzzahlige Werte ohne Nachkommastellen."""
    x = round(float(x), 6)
    if x.is_integer():
        return num(int(x))
    whole, frac = _half_up(x, digits).split(".")
    return f"{num(int(whole))},{frac}"


def percent_text(x: float) -> str:
    """Anteil als Prozent, ganzzahlig (Komma-frei)."""
    return _half_up(x * 100, 0) + " %"


def sigma_text(sigma: float) -> str:
    """Streuung des Schätzfehlers mit Komma: 0, 0,05, 0,2, 1, 4."""
    return f"{sigma:g}".replace(".", ",")


def sigma_key(sigma: float) -> str:
    return f"{sigma:g}"


def _le(x: float, limit: float) -> bool:
    """x <= limit mit Toleranz für Gleitkommarauschen."""
    return round(x, 9) <= limit


# ---------------------------------------------------------------- Verdikte einer Stichprobe

def verdict_sample(stats: dict, name: str, sigma: float) -> tuple[str, str]:
    """Verdikt der Kernfrage: wie viel der Lücke zwischen „niedrigster Stapel“ und vollem Wissen schließt die Schätzung?"""
    text = (f"{name}: Der niedrigste Stapel kostet im Mittel {dec(stats['lowest'])} Umlagerungen, die Regel mit vollem Wissen {dec(stats['full'])}, "
            f"mit Schätzfehler {sigma_text(sigma)} {dec(stats['tight'])}.")
    c = stats["closed"]
    if c is None:
        return "info", text + " Hier gibt es keine Lücke: Das volle Wissen ist nicht besser als der niedrigste Stapel."
    text += f" Die Schätzung schließt {percent_text(c)} der Lücke."
    if _le(C.CLOSED_BIG, c):
        return "success", text + " Sie trägt."
    if _le(C.CLOSED_HALF, c):
        return "info", text + " Sie trägt zum Teil."
    if c < 0:
        return "warning", text + " Im Mittel ist sie schlechter als der niedrigste Stapel."
    return "warning", text + " Sie trägt kaum."


def bound_line(stats: dict) -> str | None:
    """Zusatzzeile mit der Untergrenze der besten Ablage und dem exakten Optimum (None, wenn nicht gerechnet)."""
    if "lb" not in stats:
        return None
    text = f"Untergrenze der besten Ablage (Blocker der besten fertigen Bucht): im Mittel {dec(stats['lb'])} Umlagerungen; Regel mit vollem Wissen {dec(stats['full'])}"
    if "exact" in stats:
        text += f"; exaktes Optimum nach der Ablage mit Schätzung {dec(stats['exact'])} (Regel beim Abruf {dec(stats['tight'])})"
    return text + "."


def result_rows(stats: dict) -> list[dict]:
    """Zeilen der Ergebnistabelle: Umlagerungen je Einlege-Regel (Mittel) und Untergrenze."""
    rows = [{"name": "Untergrenze der besten Ablage", "value": dec(stats["lb"]) if "lb" in stats else "nicht gerechnet"},
            {"name": "engste Passung mit vollem Wissen", "value": dec(stats["full"])},
            {"name": "engste Passung nach Schätzung", "value": dec(stats["tight"])},
            {"name": "niedrigster Stapel", "value": dec(stats["lowest"])},
            {"name": "zufälliger Stapel", "value": dec(stats["random"])}]
    return rows


# ---------------------------------------------------------------- Stichproben (vorberechnet)

def sigma_rows(stacks: int, height: int, n: int, seeds, sigmas=C.SIGMA_OPTIONS) -> list[dict]:
    """Je Bucht: Umlagerungen für random, lowest und tight bei jedem sigma."""
    rows = []
    for sd in seeds:
        arr = A.make_arrivals(n, sd)
        row = {"seed": sd, "random": A.relocations(A.place(arr, stacks, height, "random", 0.0, sd), height), "lowest": A.relocations(A.place(arr, stacks, height, "lowest", 0.0, sd), height),
               "tight": {}}
        for sg in sigmas:
            row["tight"][sigma_key(sg)] = A.relocations(A.place(arr, stacks, height, "tight", sg, sd), height)
        rows.append(row)
    return rows


def sigma_stats(rows: list[dict], sigmas=C.SIGMA_OPTIONS) -> dict:
    """Je Zelle: Mittel von random und lowest, je sigma das Mittel von tight und der Anteil der geschlossenen Lücke; Kipppunkt = kleinstes sigma, bei dem tight mindestens so viel kostet wie lowest."""
    low, rnd = mean(r["lowest"] for r in rows), mean(r["random"] for r in rows)
    tight = {sigma_key(sg): mean(r["tight"][sigma_key(sg)] for r in rows) for sg in sigmas}
    full = tight[sigma_key(0.0)]
    kipp = next((sg for sg in sigmas if _le(low, tight[sigma_key(sg)])), None)
    return {"n": len(rows), "random": rnd, "lowest": low, "tight": tight, "closed": {k: closed_share(low, v, full) for k, v in tight.items()}, "kipp": kipp}


def lb_rows(stacks: int, height: int, n: int, seeds, sigmas=C.LB_SIGMAS) -> list[dict]:
    """Je Bucht: Untergrenze der Ablage, random und lowest (Regel beim Abruf) und je sigma die Kosten der Regel und das exakte Optimum nach `tight`."""
    rows = []
    for sd in seeds:
        arr = A.make_arrivals(n, sd)
        row = {"seed": sd, "lb": A.min_blockers_storing(arr, stacks, height), "random": A.relocations(A.place(arr, stacks, height, "random", 0.0, sd), height),
               "lowest": A.relocations(A.place(arr, stacks, height, "lowest", 0.0, sd), height), "greedy": {}, "exact": {}}
        for sg in sigmas:
            bay = A.place(arr, stacks, height, "tight", sg, sd)
            row["greedy"][sigma_key(sg)] = A.relocations(bay, height)
            row["exact"][sigma_key(sg)] = A.reloc_search(bay, height, C.BAND_EXACT_CAP).optimum
        rows.append(row)
    return rows


def lb_stats(rows: list[dict], sigmas=C.LB_SIGMAS) -> dict:
    """Je Zelle: Mittel der Untergrenze, von random und lowest, je sigma Mittel von Regel und exaktem Optimum, Zahl der Verletzungen von Untergrenze ≤ exakt ≤ Regel."""
    out = {"n": len(rows), "lb": mean(r["lb"] for r in rows), "random": mean(r["random"] for r in rows), "lowest": mean(r["lowest"] for r in rows), "greedy": {}, "exact": {}, "violations": 0}
    for sg in sigmas:
        k = sigma_key(sg)
        out["greedy"][k] = mean(r["greedy"][k] for r in rows)
        solved = [r["exact"][k] for r in rows if r["exact"][k] is not None]
        out["exact"][k] = mean(solved) if solved else None                                      # Buchten am Knotenlimit zählen nicht in den Mittelwert, aber als Verletzung der Prüfkette
        out["violations"] += sum(1 for r in rows if r["exact"][k] is None or not r["lb"] <= r["exact"][k] <= r["greedy"][k])
    return out


def key(stacks: int, height: int, n: int) -> str:
    return f"{stacks},{height},{n}"


def load_bands() -> dict:
    """Vorberechnete Kennzahlen, erzeugt von generate_precomputed.py: {"sigma": {"s,h,n": sigma_stats}, "lb": {"s,h,n": lb_stats}}."""
    return json.loads(BANDS_FILE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- Verdikte der Tabellen

def verdict_kipp(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „ab welchem Schätzfehler ist die Schätzung nicht mehr besser als der niedrigste Stapel?“ für eine Zelle."""
    k = stats["kipp"]
    last = C.SIGMA_OPTIONS[-1]
    if k is None:
        return "info", f"{name}: Bis zum Schätzfehler {sigma_text(last)} kostet die Regel mit Schätzung weniger als der niedrigste Stapel ({dec(stats['lowest'])} Umlagerungen); einen Kipppunkt gibt es im untersuchten Bereich nicht."
    prev = max((sg for sg in C.SIGMA_OPTIONS if sg < k), default=None)
    where = f"zwischen {sigma_text(prev)} und {sigma_text(k)}" if prev is not None else f"schon bei {sigma_text(k)}"
    return "warning", (f"{name}: Der Kipppunkt liegt {where}: Dort kostet die Regel mit Schätzung ({dec(stats['tight'][sigma_key(k)])}) so viel wie oder mehr als der niedrigste Stapel "
                       f"({dec(stats['lowest'])}). Ab hier ist kein Vorteil mehr zu sehen; kleine Unterschiede liegen im Messrauschen.")


def verdict_bound(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „wie nah ist das volle Wissen an der Untergrenze der besten Ablage?“ für eine Zelle mit Untergrenze."""
    full = stats["greedy"][sigma_key(0.0)]
    gap = full - stats["lb"]
    text = (f"{name}: Die Untergrenze der besten Ablage liegt bei {dec(stats['lb'])} Umlagerungen, die Regel mit vollem Wissen bei {dec(full)}, der niedrigste Stapel bei {dec(stats['lowest'])}: "
            f"Mit vollem Wissen fehlen {dec(gap)} bis zur Untergrenze, ohne Wissen {dec(stats['lowest'] - stats['lb'])}.")
    if _le(gap, C.GAP_NEAR):
        return "success", text + " Das volle Wissen liegt nahe an der Untergrenze."
    return "info", text + " Das volle Wissen liegt noch deutlich über der Untergrenze."
