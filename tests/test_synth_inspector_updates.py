import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import synth_preset_inspector_handler as spih


def create_basic_preset(path, custom_name="Old", vol=0.5):
    preset = {
        "kind": "instrumentRack",
        "parameters": {"Macro0": 0.0},
        "chains": [
            {
                "devices": [
                    {
                        "kind": "drift",
                        "parameters": {
                            "Macro0": {"value": 0.0, "customName": custom_name},
                            "Volume": vol,
                        },
                    }
                ]
            }
        ],
    }
    Path(path).write_text(json.dumps(preset))


def test_update_macro_names(tmp_path):
    p = tmp_path / "preset.json"
    create_basic_preset(p)

    res = spih.update_preset_macro_names(str(p), {0: "New"})
    assert res["success"], res.get("message")
    with open(p) as f:
        data = json.load(f)
    assert data["chains"][0]["devices"][0]["parameters"]["Macro0"]["customName"] == "New"
    assert data["parameters"]["Macro0"] == 0.0

    res = spih.update_preset_macro_names(str(p), {0: ""})
    assert res["success"]
    with open(p) as f:
        data = json.load(f)
    assert "customName" not in data["chains"][0]["devices"][0]["parameters"]["Macro0"]


def test_update_and_delete_parameter_mapping(tmp_path):
    p = tmp_path / "preset.json"
    create_basic_preset(p)

    res = spih.update_preset_parameter_mappings(
        str(p), {0: {"parameter_path": "chains[0].devices[0].parameters.Volume"}}
    )
    assert res["success"], res.get("message")
    with open(p) as f:
        data = json.load(f)
    vol = data["chains"][0]["devices"][0]["parameters"]["Volume"]
    assert vol["value"] == 0.5
    assert vol["macroMapping"]["macroIndex"] == 0

    res = spih.delete_parameter_mapping(str(p), "chains[0].devices[0].parameters.Volume")
    assert res["success"], res.get("message")
    with open(p) as f:
        data = json.load(f)
    assert data["chains"][0]["devices"][0]["parameters"]["Volume"] == 0.5


def test_scan_for_synth_presets(monkeypatch, tmp_path):
    preset_path = tmp_path / "Preset.ablpreset"
    create_basic_preset(preset_path)

    base = "/data/UserData/UserLibrary/Track Presets"
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

    monkeypatch.setattr(spih.os.path, "join", fake_join)
    monkeypatch.setattr(spih.os.path, "exists", fake_exists)
    monkeypatch.setattr(spih.os, "walk", fake_walk)
    monkeypatch.setattr(spih, "get_cache", lambda k: None)
    captured = {}
    monkeypatch.setattr(spih, "set_cache", lambda k, v: captured.setdefault("data", v))

    result = spih.scan_for_synth_presets()
    assert result["success"]
    assert result["presets"] == captured["data"]
    assert result["presets"][0]["name"] == "Preset"

    monkeypatch.setattr(spih, "get_cache", lambda k: captured["data"])
    result_cached = spih.scan_for_synth_presets()
    assert "cached" in result_cached["message"]
