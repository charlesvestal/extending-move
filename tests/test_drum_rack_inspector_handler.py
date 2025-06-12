import json
import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import drum_rack_inspector_handler as drih


def create_simple_preset(path, sample_uri="file:///orig.wav"):
    preset = {
        "kind": "instrumentRack",
        "chains": [
            {
                "devices": [
                    {
                        "kind": "drumRack",
                        "chains": [
                            {
                                "devices": [
                                    {
                                        "kind": "drumCell",
                                        "deviceData": {"sampleUri": sample_uri},
                                        "parameters": {
                                            "Voice_PlaybackStart": 0.0,
                                            "Voice_PlaybackLength": 1.0,
                                        },
                                    }
                                ]
                            }
                        ],
                    }
                ]
            }
        ]
    }
    Path(path).write_text(json.dumps(preset))


def test_update_and_get_samples(tmp_path):
    preset = tmp_path / "preset.json"
    create_simple_preset(preset)

    new_path = "/data/UserData/UserLibrary/Samples/kick 1.wav"
    ok, msg = drih.update_drum_cell_sample(
        str(preset), 1, new_path, new_playback_start=0.2, new_playback_length=0.5
    )
    assert ok, msg

    info = drih.get_drum_cell_samples(str(preset))
    assert info["success"], info.get("message")
    assert len(info["samples"]) == 1
    sample = info["samples"][0]
    assert sample["pad"] == 1
    assert sample["path"].endswith("kick 1.wav")
    assert sample["playback_start"] == pytest.approx(0.2)
    assert sample["playback_length"] == pytest.approx(0.5)

    with open(preset) as f:
        data = json.load(f)
    cell = data["chains"][0]["devices"][0]["chains"][0]["devices"][0]
    assert cell["deviceData"]["sampleUri"] == "ableton:/user-library/Samples/kick%201.wav"


def test_find_original_sample(tmp_path):
    base = tmp_path / "snare.wav"
    base.write_text("x")
    derived = tmp_path / "snare_reversed.wav"
    derived.write_text("y")
    assert drih.find_original_sample(str(derived)) == str(base)


def test_scan_for_drum_rack_presets(monkeypatch, tmp_path):
    base = "/data/UserData/UserLibrary/Track Presets"
    (tmp_path / "Preset.json").write_text(json.dumps({"kind": "drumRack"}))

    real_join = os.path.join
    real_exists = os.path.exists
    real_walk = os.walk

    def fake_join(a, *p):
        if a == base:
            return real_join(str(tmp_path), *p)
        return real_join(a, *p)

    def fake_exists(path):
        if path == base:
            return True
        return real_exists(path)

    def fake_walk(path):
        if path == base:
            for item in real_walk(str(tmp_path)):
                yield base, item[1], item[2]
            return
        yield from real_walk(path)

    monkeypatch.setattr(drih.os.path, "join", fake_join)
    monkeypatch.setattr(drih.os.path, "exists", fake_exists)
    monkeypatch.setattr(drih.os, "walk", fake_walk)
    monkeypatch.setattr(drih, "get_cache", lambda k: None)
    captured = {}
    monkeypatch.setattr(drih, "set_cache", lambda k, v: captured.setdefault("data", v))

    result = drih.scan_for_drum_rack_presets()
    assert result["success"]
    assert result["presets"] == captured["data"]
    assert result["presets"][0]["name"] == "Preset"

    # Simulate cached call
    monkeypatch.setattr(drih, "get_cache", lambda k: captured["data"])
    result_cached = drih.scan_for_drum_rack_presets()
    assert "cached" in result_cached["message"]


def test_get_samples_core_library_translation(tmp_path):
    preset = tmp_path / "preset.json"
    uri = (
        "ableton:/packs/abl-core-library/"
        "Samples/Drums/Snare/Snare 606.aif"
    )
    create_simple_preset(preset, sample_uri=uri)

    info = drih.get_drum_cell_samples(str(preset))
    assert info["success"], info.get("message")
    sample = info["samples"][0]
    assert sample["path"].startswith("/data/CoreLibrary/")
    assert sample["path"].endswith("Snare 606.aif")
