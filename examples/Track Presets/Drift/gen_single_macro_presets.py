#!/usr/bin/env python3
import json
import copy
import os
import sys


def find_drift_devices(obj):
    """Recursively find all drift devices in obj."""
    devices = []
    if isinstance(obj, dict):
        if obj.get("kind") == "drift":
            devices.append(obj)
        for v in obj.values():
            devices.extend(find_drift_devices(v))
    elif isinstance(obj, list):
        for item in obj:
            devices.extend(find_drift_devices(item))
    return devices


def remove_macro_mappings(obj):
    """Remove all macroMapping entries from preset data."""
    if isinstance(obj, dict):
        obj.pop("macroMapping", None)
        for v in obj.values():
            remove_macro_mappings(v)
    elif isinstance(obj, list):
        for item in obj:
            remove_macro_mappings(item)


def main(template_path="Analog Shape - Core.json", out_dir="macro_presets"):
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    drift_devices = find_drift_devices(template)
    if not drift_devices:
        sys.exit("Error: no drift device found in template")

    param_names = sorted(drift_devices[0].get("parameters", {}).keys())

    os.makedirs(out_dir, exist_ok=True)

    for idx, param in enumerate(param_names):
        preset = copy.deepcopy(template)
        remove_macro_mappings(preset)

        for dev in find_drift_devices(preset):
            params = dev.setdefault("parameters", {})
            if param in params:
                val = params[param]
                if isinstance(val, dict) and "value" in val:
                    base_val = val["value"]
                else:
                    base_val = val
                params[param] = {"value": base_val, "macroMapping": {"macroIndex": 0}}
        preset["name"] = param
        fname = f"{idx:03d}-{param.replace('/', '-').replace(' ', '_')}.ablpreset"
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as out:
            json.dump(preset, out, indent=2, ensure_ascii=False)
        print(f"Wrote {fname}")


if __name__ == "__main__":
    tpl = sys.argv[1] if len(sys.argv) > 1 else "Analog Shape - Core.json"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "macro_presets"
    main(tpl, out_dir)
