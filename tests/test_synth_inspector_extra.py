import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.synth_preset_inspector_handler import (
    extract_available_parameters,
    extract_parameter_values,
    load_drift_schema,
)


def create_simple_drift_preset(path):
    preset = {
        "kind": "instrumentRack",
        "chains": [
            {
                "devices": [
                    {
                        "kind": "drift",
                        "parameters": {
                            "Enabled": True,
                            "Volume": {"value": 0.75}
                        }
                    }
                ]
            }
        ]
    }
    Path(path).write_text(json.dumps(preset))


def test_load_drift_schema():
    schema = load_drift_schema()
    assert isinstance(schema, dict)
    assert "CyclingEnvelope_Hold" in schema


def test_extract_available_and_values(tmp_path):
    p = tmp_path / "preset.json"
    create_simple_drift_preset(p)
    info = extract_available_parameters(str(p))
    assert info["success"]
    assert "Volume" in info["parameters"]
    vals = extract_parameter_values(str(p))
    assert vals["success"]
    param = {p["name"]: p["value"] for p in vals["parameters"]}
    assert param["Volume"] == 0.75

