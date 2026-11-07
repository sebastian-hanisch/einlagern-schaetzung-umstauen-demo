"""Erzeugt eas_bands.json: Kennzahlen der festen Buchten (Seeds ab 0) für zwei Auswertungen.

    python generate_precomputed.py

"sigma": je Zelle aus SIGMA_CELLS (SIGMA_BAYS Buchten) die Umlagerungen beim Abruf nach zufälligem Stapel, niedrigstem Stapel und engster Passung nach Schätzung bei jedem Schätzfehler
         aus SIGMA_OPTIONS, der Anteil der geschlossenen Lücke und der Kipppunkt (sigma_stats).
"lb":    je Zelle aus LB_CELLS (LB_BAYS Buchten) zusätzlich die Untergrenze der besten Ablage und das exakte Optimum nach der Ablage mit Schätzung (lb_stats).

Rechenzeit unter fünf Minuten (die Zelle 4 x 4 x 10 mit Untergrenze und exakter Suche ist die langsamste; die Zellen laufen in getrennten Prozessen). Dieselben Funktionen wie die Tests
(`eas_evaluation.sigma_rows`, `sigma_stats`, `lb_rows`, `lb_stats`); die Datei speichert nur Kennzahlen, keine Zeilen. Rauschen und Zufallsregel kommen aus random.Random(seed): deterministisch."""

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import eas_constants as C
import eas_evaluation as ev

sys.stdout.reconfigure(encoding="utf-8")


def job(kind, stacks, height, n):
    k = ev.key(stacks, height, n)
    if kind == "sigma":
        return "sigma", k, ev.sigma_stats(ev.sigma_rows(stacks, height, n, range(C.SIGMA_BAYS)))
    return "lb", k, ev.lb_stats(ev.lb_rows(stacks, height, n, range(C.LB_BAYS)))


def main():
    tasks = [("lb", s, h, n) for s, h, n in reversed(C.LB_CELLS)] + [("sigma", s, h, n) for s, h, n in reversed(C.SIGMA_CELLS)]
    out = {"sigma": {}, "lb": {}}
    with ProcessPoolExecutor(max_workers=max(2, (os.cpu_count() or 4) - 2)) as pool:
        futures = {pool.submit(job, *t): t for t in tasks}
        for fut in as_completed(futures):
            kind, k, stats = fut.result()
            out[kind][k] = stats
            print(kind, k, "fertig", flush=True)
    with open("eas_bands.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("geschrieben: eas_bands.json", flush=True)


if __name__ == "__main__":
    main()
