#!/usr/bin/env python3
"""Generate Drift presets with boundary values for each parameter.

This script iterates over all parameters present in the example
`Analog Shape` preset and creates copies of the preset with the
parameter set to -1, 0, 0.5, and 1. The results are written to a CSV
file along with whether each generated preset still passes the schema
validation check.
"""

from pathlib import Path
import argparse
import csv
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.synth_preset_inspector_handler import (
    load_drift_schema,
    extract_available_parameters,
    extract_parameter_values,
)
from core.synth_param_editor_handler import update_parameter_values

TEST_VALUES = [-1, 0, 0.5, 1]
BASE_PRESET = Path("examples/Track Presets/Drift/Analog Shape.ablpreset")
SCHEMA = load_drift_schema()


def validate_value(name: str, value):
    """Return True if *value* conforms to the schema entry for *name*."""
    meta = SCHEMA.get(name)
    if not meta:
        return True
    typ = meta.get("type")
    if typ == "number":
        if meta.get("min") is not None and value < meta["min"]:
            return False
        if meta.get("max") is not None and value > meta["max"]:
            return False
        if meta.get("decimals") == 0 and not float(value).is_integer():
            return False
    elif typ == "boolean":
        if value not in (0, 1, True, False):
            return False
    elif typ == "enum":
        if value not in meta.get("options", []):
            return False
    return True


def main(output_dir: str) -> None:
    info = extract_available_parameters(str(BASE_PRESET))
    if not info["success"]:
        raise RuntimeError(info["message"])

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "results.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "value", "update_success", "valid"])

        for param in sorted(info["parameters"]):
            for val in TEST_VALUES:
                safe_name = param.replace("/", "_").replace(" ", "_")
                dest = out_dir / f"{safe_name}_{val}.ablpreset"
                result = update_parameter_values(
                    str(BASE_PRESET), {param: str(val)}, str(dest)
                )
                valid = False
                if result["success"]:
                    vals = extract_parameter_values(str(dest))
                    if vals["success"]:
                        param_vals = {
                            p["name"]: p["value"] for p in vals["parameters"]
                        }
                        valid = validate_value(param, param_vals.get(param))
                writer.writerow([param, val, result["success"], valid])
                status = "OK" if result["success"] else "FAIL"
                print(f"{param}={val}: {status}, valid={valid}")

    print(f"Results written to {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create test presets for all Drift parameters"
    )
    parser.add_argument(
        "--output-dir",
        default="generated_presets",
        help="Directory where presets and results.csv will be written",
    )
    args = parser.parse_args()
    main(args.output_dir)
