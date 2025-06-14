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
        track["devices"].append(
            {"kind": "drift", "parameters": {"Osc1Gain": {"id": 1}}}
        )
        clip["envelopes"].append(
            {"parameterId": 1, "breakpoints": [{"time": 0.0, "value": 0.5}]}
        )
    song = {"tracks": [track]}
    Path(path).write_text(json.dumps(song))


def test_generate_pad_grid():
    handler = SetInspectorHandler()
    html = handler.generate_pad_grid(
        {0, 31}, {0: 1, 31: 2}, {0: "A", 31: "B"}, selected_idx=31
    )
    # Should create 32 cells with two occupied
    assert html.count('class="pad-cell occupied"') == 2
    assert html.count('name="pad_index"') == 32
    # Selected pad should have "checked" attribute
    assert 'inspect_pad_32" name="pad_index" value="32" checked' in html


def test_generate_pad_grid_pitch_mark():
    handler = SetInspectorHandler()
    html = handler.generate_pad_grid(
        {0}, {0: 1}, {0: "A"}, selected_idx=0, pitch_pads={36}
    )
    assert "pitch-mark" in html


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
    monkeypatch.setattr(
        sih,
        "load_drift_schema",
        lambda: {"Osc1Gain": {"min": 0.0, "max": 1.0, "unit": "pct"}},
    )
    monkeypatch.setattr(sih, "load_wavetable_schema", lambda: {})
    monkeypatch.setattr(sih, "load_melodic_sampler_schema", lambda: {})

    data = sih.get_clip_data(str(set_path), 0, 0)
    assert data["success"], data.get("message")
    # Parameter mappings and ranges should be extracted
    assert data["param_map"][1] == "Osc1Gain"
    assert data["param_ranges"][1]["max"] == 1.0
    env = data["envelopes"][0]
    assert env["rangeMin"] == 0.0 and env["rangeMax"] == 1.0


def test_pitch_conversion_roundtrip():
    notes = [
        {
            "noteNumber": 36,
            "startTime": 0.0,
            "duration": 1.0,
            "pitchBend": 170.6458282470703,
        },
        {
            "noteNumber": 36,
            "startTime": 1.0,
            "duration": 1.0,
            "pitchBend": -170.6458282470703,
        },
    ]
    steps = sih.notes_to_pitch_steps(notes, 36)
    assert steps[0]["noteNumber"] == 37
    assert steps[1]["noteNumber"] == 35
    recon = sih.steps_to_pitch_notes(steps, 36)
    assert abs(recon[0]["pitchBend"] - notes[0]["pitchBend"]) < 1e-6
    assert abs(recon[1]["pitchBend"] - notes[1]["pitchBend"]) < 1e-6


def test_pitch_bend_pad_detection():
    notes = [
        {"noteNumber": 36, "pitchBend": 10.0},
        {"noteNumber": 37, "pitchBend": 0.0},
        {"noteNumber": 38, "pitchBend": -5.0},
    ]
    pads = sih.pitch_bend_pads(notes)
    assert pads == [36, 38]
