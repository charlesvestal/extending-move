import json
from pathlib import Path
from core import synth_preset_inspector_handler as spih


def create_preset(path, mods=None):
    if mods is None:
        mods = {"ParamA": [0.1] * 13}
    preset = {
        "kind": "instrumentRack",
        "chains": [
            {
                "devices": [
                    {"kind": "wavetable", "deviceData": {"modulations": mods}}
                ]
            }
        ],
    }
    Path(path).write_text(json.dumps(preset))


def test_extract_mod_matrix(tmp_path):
    p = tmp_path / "preset.json"
    create_preset(p)
    res = spih.extract_wavetable_mod_matrix(str(p))
    assert res["success"], res.get("message")
    assert res["matrix"][0]["name"] == "ParamA"
    assert len(res["matrix"][0]["values"]) == 11


def test_update_mod_matrix(tmp_path):
    p = tmp_path / "preset.json"
    create_preset(p)
    matrix = [{"name": "ParamB", "values": [0.2] * 11, "extra": [1, 2]}]
    res = spih.update_wavetable_mod_matrix(str(p), matrix)
    assert res["success"], res.get("message")
    res2 = spih.extract_wavetable_mod_matrix(str(p))
    names = [r["name"] for r in res2["matrix"]]
    assert "ParamB" in names
    for row in res2["matrix"]:
        if row["name"] == "ParamB":
            assert row["values"][0] == 0.2
            assert row.get("extra") == [1, 2]
            break

