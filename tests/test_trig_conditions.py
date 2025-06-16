import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.trig_conditions import apply_trig_conditions


def test_ratio_condition_expansion():
    notes = [
        {"noteNumber": 60, "startTime": 0.0, "duration": 0.5, "velocity": 100, "cond": "1:4"},
        {"noteNumber": 62, "startTime": 1.0, "duration": 0.5, "velocity": 100}
    ]
    new_notes, region, loop_end = apply_trig_conditions(notes, 0.0, 2.0, 2.0)
    starts = [n["startTime"] for n in new_notes if n["noteNumber"] == 62]
    assert region == 8.0
    assert loop_end == 8.0
    assert starts == [1.0, 3.0, 5.0, 7.0]
    assert sum(1 for n in new_notes if n["noteNumber"] == 60) == 1


def test_probability_condition():
    notes = [
        {"noteNumber": 60, "startTime": 0.0, "duration": 1.0, "velocity": 100, "cond": "p50"}
    ]
    new_notes, region, loop_end = apply_trig_conditions(notes, 0.0, 1.0, 1.0)
    assert region == 2.0
    assert loop_end == 2.0
    assert len(new_notes) == 1
