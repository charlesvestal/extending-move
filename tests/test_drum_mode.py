import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from core.drum_mode import enforce_drum_mode

def test_simple_overlap():
    notes = [
        {"startTime": 0.0, "duration": 1.0},
        {"startTime": 0.5, "duration": 1.0},
    ]
    enforce_drum_mode(notes)
    assert notes[0]["duration"] == 0.5


def test_chained_overlap():
    notes = [
        {"startTime": 0.0, "duration": 1.0},
        {"startTime": 0.8, "duration": 0.4},
        {"startTime": 1.1, "duration": 0.9},
    ]
    enforce_drum_mode(notes)
    assert notes[0]["duration"] == 0.8
    assert notes[1]["duration"] == pytest.approx(0.3)


def test_zero_or_negative():
    notes = [
        {"startTime": 0.0, "duration": 0.5},
        {"startTime": 0.4, "duration": 0.5},
    ]
    enforce_drum_mode(notes)
    assert notes[0]["duration"] == pytest.approx(0.4)
    assert notes[1]["startTime"] == 0.4
