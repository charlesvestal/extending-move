import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers.set_inspector_handler_class import SetInspectorHandler
from core import set_inspector_handler as sih


def create_simple_set(path, with_params=False):
    """Create a minimal Ableton set for testing."""
    clip = {
        "name": "Clip1",
        "notes": [],
        "envelopes": [],
        "region": {"end": 4.0},
    }
    track = {
        "name": "Track1",
        "devices": [],
        "clipSlots": [{"clip": clip}],
    }
    if with_params:
        track["devices"].append({
            "kind": "drift",
            "parameters": {"Osc1Gain": {"id": 1}}
        })
        clip["envelopes"].append({"parameterId": 1, "breakpoints": [{"time": 0.0, "value": 0.5}]})
    song = {"tracks": [track]}
    Path(path).write_text(json.dumps(song))


def test_generate_pad_grid():
    handler = SetInspectorHandler()
    html = handler.generate_pad_grid({0, 31}, {0: 1, 31: 2}, {0: "A", 31: "B"}, selected_idx=31)
    # Should create 32 cells with two occupied
    assert html.count('class="pad-cell occupied"') == 2
    assert html.count('name="pad_index"') == 32
    # Selected pad should have "checked" attribute
    assert 'inspect_pad_32" name="pad_index" value="32" checked' in html


def test_generate_clip_grid():
    handler = SetInspectorHandler()
    clips = [
        {"track": 0, "clip": 0, "name": "One", "color": 1},
        {"track": 1, "clip": 1, "name": "Two", "color": 2},
    ]
    html = handler.generate_clip_grid(clips, selected="0:0")
    # Default grid is 4x8
    assert html.count('name="clip_select"') == 32
    # Occupied cells should be marked and first clip selected
    assert 'clip_0_0" name="clip_select" value="0:0" checked' in html
    assert html.count('class="pad-cell occupied"') == 2


def test_list_clips(tmp_path):
    set_path = tmp_path / "set.abl"
    create_simple_set(set_path)
    result = sih.list_clips(str(set_path))
    assert result["success"], result.get("message")
    clips = result.get("clips", [])
    assert clips and clips[0]["name"] == "Clip1"
    assert clips[0]["track"] == 0 and clips[0]["clip"] == 0


def test_get_clip_data_param_ranges(monkeypatch, tmp_path):
    set_path = tmp_path / "set.abl"
    create_simple_set(set_path, with_params=True)

    # Provide simple schema for parameter range lookup
    monkeypatch.setattr(sih, "load_drift_schema", lambda: {"Osc1Gain": {"min": 0.0, "max": 1.0, "unit": "pct"}})
    monkeypatch.setattr(sih, "load_wavetable_schema", lambda: {})
    monkeypatch.setattr(sih, "load_melodic_sampler_schema", lambda: {})

    data = sih.get_clip_data(str(set_path), 0, 0)
    assert data["success"], data.get("message")
    # Parameter mappings and ranges should be extracted
    assert data["param_map"][1] == "Osc1Gain"
    assert data["param_ranges"][1]["max"] == 1.0
    env = data["envelopes"][0]
    assert env["rangeMin"] == 0.0 and env["rangeMax"] == 1.0


def test_set_round_trip_no_changes(tmp_path):
    """Loading and saving demo sets without edits should not alter them."""
    demo_dir = Path("examples/Sets/Move")
    for src in demo_dir.glob("*.abl"):
        original = src.read_bytes()
        dest = tmp_path / src.name
        dest.write_bytes(original)

        with open(dest) as f:
            song = json.load(f)

        for ti, track in enumerate(song.get("tracks", [])):
            for ci, slot in enumerate(track.get("clipSlots", [])):
                if not slot.get("clip"):
                    continue
                data = sih.get_clip_data(str(dest), ti, ci)
                assert data["success"], data.get("message")
                result = sih.save_clip(
                    str(dest),
                    ti,
                    ci,
                    data["notes"],
                    data["envelopes"],
                    data["region"],
                    data["loop_start"],
                    data["loop_end"],
                )
                assert result["success"], result.get("message")

        assert dest.read_bytes() == original


def test_pitchbend_edit_preserves_other_automations(tmp_path):
    set_path = tmp_path / "set.abl"
    create_simple_set(set_path)

    with open(set_path) as f:
        song = json.load(f)

    clip = song["tracks"][0]["clipSlots"][0]["clip"]
    clip["notes"] = [
        {
            "noteNumber": 60,
            "startTime": 0.0,
            "duration": 1.0,
            "velocity": 100.0,
            "offVelocity": 0.0,
            "automations": {
                "PitchBend": [
                    {"time": 0.0, "value": 100.0},
                    {"time": 0.5, "value": -100.0},
                ],
                "Pressure": [{"time": 0.25, "value": 0.5}],
            },
        }
    ]

    with open(set_path, "w") as f:
        json.dump(song, f)

    data = sih.get_clip_data(str(set_path), 0, 0)
    assert data["success"], data.get("message")
    notes = data["notes"]
    assert notes and notes[0]["noteNumber"] == 60

    val = (62 - 36) * 170.6458282470703
    notes[0]["automations"]["PitchBend"] = [{"time": 0.0, "value": val}]

    result = sih.save_clip(
        str(set_path),
        0,
        0,
        notes,
        data["envelopes"],
        data["region"],
        data["loop_start"],
        data["loop_end"],
    )
    assert result["success"], result.get("message")

    with open(set_path) as f:
        saved = json.load(f)
    saved_note = saved["tracks"][0]["clipSlots"][0]["clip"]["notes"][0]
    assert "Pressure" in saved_note["automations"]
    assert saved_note["automations"]["Pressure"] == [{"time": 0.25, "value": 0.5}]
    pb = saved_note["automations"]["PitchBend"]
    assert len(pb) == 1 and pb[0]["time"] == 0.0
    assert abs(pb[0]["value"] - val) < 1e-6
