import json
from pathlib import Path

from core.effect_chain_handler import extract_effect_parameters, apply_macro_mappings


def create_fx_preset(path: Path):
    preset = {
        "kind": "audioEffectRack",
        "parameters": {"Macro0": 0.0},
        "chains": [
            {
                "devices": [
                    {
                        "kind": "channelEq",
                        "parameters": {"Gain": 1.0},
                    }
                ]
            }
        ],
    }
    path.write_text(json.dumps(preset))


def test_extract_effect_parameters(tmp_path):
    p = tmp_path / "preset.json"
    create_fx_preset(p)
    res = extract_effect_parameters(str(p))
    assert res["success"], res.get("message")
    param = res["parameters"][0]
    assert param["name"] == "Gain"
    assert param["path"].endswith("Gain")


def test_apply_macro_mappings(tmp_path):
    p = tmp_path / "preset.json"
    create_fx_preset(p)
    dest = tmp_path / "out.ablpreset"
    mappings = {0: {"parameter": "Gain", "parameter_path": "chains[0].devices[0].parameters.Gain"}}
    res = apply_macro_mappings(str(p), mappings, str(dest), {0: "Volume"})
    assert res["success"], res.get("message")
    with open(dest) as f:
        data = json.load(f)
    gain = data["chains"][0]["devices"][0]["parameters"]["Gain"]
    assert gain["macroMapping"]["macroIndex"] == 0
    assert data["parameters"]["Macro0"] == 0.0

