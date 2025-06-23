import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core import fx_chain_handler as fch


def make_preset(path, kind="autoFilter"):
    data = {
        "kind": kind,
        "parameters": {"Gain": 0.5, "Enabled": True},
        "deviceData": {},
    }
    Path(path).write_text(json.dumps(data))


def test_load_fx_presets(monkeypatch, tmp_path):
    base = tmp_path / "Audio Effects"
    pdir = base / "Saturator"
    pdir.mkdir(parents=True)
    make_preset(pdir / "Default.json", kind="saturator")
    presets = fch.load_fx_presets(str(base))
    assert "Saturator" in presets
    assert "Default" in presets["Saturator"]
    info = presets["Saturator"]["Default"]
    assert info["parameters"]["Gain"] == 0.5


def test_create_fx_chain(monkeypatch, tmp_path):
    preset = tmp_path / "preset.json"
    make_preset(preset, kind="saturator")
    monkeypatch.setattr(fch, "USER_FX_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(fch, "refresh_library", lambda: None)
    result = fch.create_fx_chain([str(preset)], {0: {"effect_index": 0, "parameter": "Gain"}}, "Test", {0: {"Gain": 0.8}})
    assert result["success"], result.get("message")
    out = Path(result["path"])
    with open(out) as f:
        data = json.load(f)
    dev = data["chains"][0]["devices"][0]
    assert dev["parameters"]["Gain"]["value"] == 0.8
    assert data["parameters"]["Macro0"]["customName"] == "Gain"
