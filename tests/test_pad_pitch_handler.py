import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.pad_pitch_handler import extract_pad_clip, save_pad_clip, pads_with_pitch, SEMITONE_VALUE, BASE_NOTE


def create_pad_set(path):
    note1 = {
        "noteNumber": 40,
        "startTime": 0.0,
        "duration": 0.5,
        "velocity": 1.0,
        "offVelocity": 0.0,
        "automations": {"PitchBend": [{"time": 0.0, "value": SEMITONE_VALUE}]},
    }
    note2 = {
        "noteNumber": 40,
        "startTime": 1.0,
        "duration": 0.5,
        "velocity": 1.0,
        "offVelocity": 0.0,
        "automations": {"PitchBend": [{"time": 0.0, "value": 0.0}]},
    }
    clip = {"name": "Clip1", "notes": [note1, note2], "envelopes": [], "region": {"end": 4.0}}
    track = {"name": "Track1", "devices": [], "clipSlots": [{"clip": clip}]}
    song = {"tracks": [track]}
    Path(path).write_text(json.dumps(song))


def test_extract_and_save_pad_clip(tmp_path):
    set_path = tmp_path / "set.abl"
    create_pad_set(set_path)
    data = extract_pad_clip(str(set_path), 0, 0, 40)
    assert len(data["notes"]) == 2
    assert data["notes"][0]["noteNumber"] == BASE_NOTE + 1
    # modify and save
    data["notes"][0]["noteNumber"] = BASE_NOTE + 2
    save_pad_clip(str(set_path), 0, 0, 40, data["notes"], 4.0, 0.0, 4.0)
    new = extract_pad_clip(str(set_path), 0, 0, 40)
    assert new["notes"][0]["noteNumber"] == BASE_NOTE + 2
    with open(set_path) as f:
        song = json.load(f)
    first = song["tracks"][0]["clipSlots"][0]["clip"]["notes"][0]
    assert abs(first["automations"]["PitchBend"][0]["value"] - 2 * SEMITONE_VALUE) < 1e-4


def test_pads_with_pitch(tmp_path):
    set_path = tmp_path / "s.abl"
    create_pad_set(set_path)
    with open(set_path) as f:
        song = json.load(f)
    notes = song["tracks"][0]["clipSlots"][0]["clip"]["notes"]
    pads = pads_with_pitch(notes)
    assert pads[40]

