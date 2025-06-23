import os
import json

DEFAULT_OUTPUT_DIR = "/data/UserData/UserLibrary/Audio Effects"


def list_audio_effect_presets():
    """Return a list of available audio effect preset file paths."""
    base_dirs = [DEFAULT_OUTPUT_DIR, os.path.join("examples", "Audio Effects")]
    presets = []
    for base in base_dirs:
        if not os.path.exists(base):
            continue
        for root, _dirs, files in os.walk(base):
            for f in files:
                if f.lower().endswith((".json", ".ablpreset")):
                    presets.append(os.path.join(root, f))
    return presets


def extract_effect_parameters(preset_path):
    """Extract parameter names from an audio effect preset."""
    try:
        with open(preset_path, "r") as f:
            data = json.load(f)
        params = []
        for key in data.get("parameters", {}):
            if key != "Enabled" and not key.startswith("Macro"):
                params.append(key)
        return params
    except Exception:
        return []


def create_effect_rack(effect_paths, macro_map, output_path, name="Effect Rack"):
    """Create an audio effect rack preset."""
    try:
        devices = []
        for p in effect_paths:
            with open(p, "r") as f:
                devices.append(json.load(f))
        rack = {
            "kind": "audioEffectRack",
            "name": name,
            "parameters": {"Enabled": True},
            "chains": [
                {
                    "name": "",
                    "devices": devices,
                    "mixer": {"pan": 0.0, "volume": 0.0},
                }
            ],
        }
        for i in range(8):
            rack["parameters"][f"Macro{i}"] = 0.0
        for macro_idx, spec in macro_map.items():
            device_idx = spec.get("device_index")
            param = spec.get("parameter")
            if device_idx is None or param is None:
                continue
            if device_idx >= len(devices):
                continue
            device = devices[device_idx]
            params = device.setdefault("parameters", {})
            if param not in params:
                continue
            val = params[param]
            if isinstance(val, dict) and "value" in val:
                target = val
            else:
                params[param] = {"value": val}
                target = params[param]
            target["macroMapping"] = {"macroIndex": macro_idx}
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(rack, f, indent=2)
            f.write("\n")
        return {"success": True, "message": f"Rack saved to {output_path}", "path": output_path}
    except Exception as exc:
        return {"success": False, "message": f"Error creating rack: {exc}"}
