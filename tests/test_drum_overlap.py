import json
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import set_inspector_handler as sih


def create_drum_set(path):
    clip = {
        "name": "Clip",
        "notes": [],
        "envelopes": [],
        "region": {"end": 4.0},
    }
    track = {
        "name": "Drums",
        "devices": [{"kind": "drumRack"}],
        "clipSlots": [{"clip": clip}],
    }
    song = {"tracks": [track]}
    Path(path).write_text(json.dumps(song))


def test_truncate_overlapping_notes(tmp_path):
    set_path = tmp_path / "set.abl"
    create_drum_set(set_path)
    notes = [
        {"noteNumber": 36, "startTime": 0.0, "duration": 1.0, "velocity": 100.0, "offVelocity": 0.0},
        {"noteNumber": 36, "startTime": 0.5, "duration": 1.0, "velocity": 100.0, "offVelocity": 0.0},
    ]
    result = sih.save_clip(str(set_path), 0, 0, notes, [], 4.0, 0.0, 4.0)
    assert result["success"], result.get("message")
    data = sih.get_clip_data(str(set_path), 0, 0)
    out = data["notes"]
    assert len(out) == 2
    assert abs(out[0]["duration"] - 0.5) < 1e-6
    assert out[1]["startTime"] == 0.5

def test_overlap_after_reverse(tmp_path):
    set_path = tmp_path / "set_rev.abl"
    create_drum_set(set_path)
    notes = [
        {"noteNumber": 36, "startTime": 0.0, "duration": 1.5, "velocity": 100.0, "offVelocity": 0.0},
        {"noteNumber": 36, "startTime": 1.0, "duration": 1.0, "velocity": 100.0, "offVelocity": 0.0},
        {"noteNumber": 36, "startTime": 2.0, "duration": 1.0, "velocity": 100.0, "offVelocity": 0.0},
    ]
    # Reverse around 0-3 range
    rev = []
    start, end = 0.0, 3.0
    for n in notes:
        rev.append({**n, "startTime": start + end - (n["startTime"] + n["duration"])})
    result = sih.save_clip(str(set_path), 0, 0, rev, [], 4.0, 0.0, 4.0)
    assert result["success"], result.get("message")
    data = sih.get_clip_data(str(set_path), 0, 0)
    out = data["notes"]
    assert len(out) == 3
    assert abs(out[1]["duration"] - 0.5) < 1e-6
