import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.trig_conditions import apply_trig_conditions


def test_ratio_condition():
    notes = [
        {"noteNumber": 60, "startTime": 0.0, "duration": 1.0, "velocity": 100},
        {"noteNumber": 61, "startTime": 0.0, "duration": 1.0, "velocity": 100, "condition": "1:4"},
    ]
    out, end, cond = apply_trig_conditions(notes, 0.0, 1.0)
    assert abs(end - 4.0) < 1e-6
    count_60 = sum(1 for n in out if n["noteNumber"] == 60)
    count_61 = sum(1 for n in out if n["noteNumber"] == 61)
    assert count_60 == 4
    assert count_61 == 1


def test_lcm_conditions():
    notes = [
        {"noteNumber": 60, "startTime": 0.0, "duration": 0.5, "velocity": 100, "condition": "1:2"},
        {"noteNumber": 61, "startTime": 0.0, "duration": 0.5, "velocity": 100, "condition": "1:3"},
    ]
    out, end, cond = apply_trig_conditions(notes, 0.0, 1.0)
    assert abs(end - 6.0) < 1e-6
    count_60 = sum(1 for n in out if n["noteNumber"] == 60)
    count_61 = sum(1 for n in out if n["noteNumber"] == 61)
    assert count_60 == 3
    assert count_61 == 2


def test_save_clip_extends_region(tmp_path):
    set_path = tmp_path / "set.abl"
    song = {
        "tracks": [
            {
                "kind": "midi",
                "clipSlots": [
                    {
                        "clip": {
                            "notes": [],
                            "envelopes": [],
                            "region": {"end": 4.0},
                        }
                    }
                ],
            }
        ]
    }
    set_path.write_text(json.dumps(song))

    from core.set_inspector_handler import save_clip, get_clip_data

    notes = [
        {"noteNumber": 60, "startTime": 0.0, "duration": 1.0, "velocity": 100},
        {"noteNumber": 61, "startTime": 0.0, "duration": 1.0, "velocity": 100, "condition": "1:4"},
    ]
    result = save_clip(str(set_path), 0, 0, notes, [], 4.0, 0.0, 4.0)
    assert result["success"], result.get("message")

    data = get_clip_data(str(set_path), 0, 0)
    assert data["region"] == 16.0
    assert data["loop_end"] == 16.0
