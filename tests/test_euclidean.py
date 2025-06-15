import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.euclidean import euclidean_rhythm, apply_euclidean_fill


def test_basic_euclidean():
    assert euclidean_rhythm(8, 3) == [2, 5, 7]
    assert euclidean_rhythm(16, 5, 1) == [0, 4, 7, 10, 13]


def test_apply_fill_overwrites_only_row():
    notes = [
        {"noteNumber": 60, "startTime": 0.0, "duration": 0.25, "velocity": 100},
        {"noteNumber": 61, "startTime": 0.5, "duration": 0.25, "velocity": 100},
    ]
    new_notes = apply_euclidean_fill(notes, 60, 0.0, 1.0, 4, 2, 0, 0.25)
    # Only row 60 within region replaced
    assert all(n["noteNumber"] == 60 for n in new_notes if n["startTime"] in [0.25, 0.75])
    assert any(n["noteNumber"] == 61 for n in new_notes)
    starts = [n["startTime"] for n in new_notes if n["noteNumber"] == 60]
    assert starts == [0.25, 0.75]
