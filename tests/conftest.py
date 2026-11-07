"""Gemeinsame Fixtures: die kleinen Fälle, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def ascending():
    """Drei Container, die in der Reihenfolge ihrer Abfahrt ankommen: wahre Nummern 1, 2, 3 (der Erste fährt zuerst ab), zwei Stapel der Höchsthöhe 3.
    Niedrigster Stapel: 1 auf Stapel 1, 2 auf Stapel 2, 3 auf Stapel 1 (beide gleich hoch, kleinster Index): Bucht (1, 3), (2). Die 3 liegt über der 1: ein Blocker. Beim Abruf wandert die 3 auf Stapel 2
    (über die 2), dann muss sie für die 2 noch einmal weg: 2 Umlagerungen.
    Engste Passung mit vollem Wissen: 1 auf Stapel 1; die 2 findet keinen sicheren Stapel (Minimum 1 < 2), nimmt den leeren Stapel 2; die 3 findet keinen (Minima 1 und 2), nimmt den mit dem größeren
    Minimum, Stapel 2: Bucht (1), (2, 3). Ein Blocker (die 3), beim Abruf eine Umlagerung (auf den leeren Platz von Stapel 1). Untergrenze der besten Ablage: 1."""
    return [1, 2, 3], 2, 3


@pytest.fixture
def sortable():
    """Wahre Nummern 2, 3, 1 in dieser Ankunftsreihenfolge, zwei Stapel der Höchsthöhe 3: Mit vollem Wissen entsteht (2, 1), (3): sortiert, 0 Umlagerungen, Untergrenze 0."""
    return [2, 3, 1], 2, 3
