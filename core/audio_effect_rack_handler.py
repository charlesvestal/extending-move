import os
import json

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "schemas")

DEFAULT_OUTPUT_DIR = "/data/UserData/UserLibrary/Audio Effects"

SUPPORTED_DEVICES = [
    "autoFilter",
    "reverb",
    "redux2",
    "phaser",
    "delay",
    "compressor",
    "chorus",
    "channelEq",
    "saturator",
]


def load_effect_schema(kind):
    """Load the parameter schema for a given device kind."""
    path = os.path.join(SCHEMA_DIR, f"{kind}_schema.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def list_available_devices():
    """Return the list of supported device kinds."""
    return SUPPORTED_DEVICES


def extract_effect_parameters(kind):
    """Return a list of parameter names for the given device kind."""
    schema = load_effect_schema(kind)
    params = []
    for name in schema.keys():
        if name != "Enabled" and not name.startswith("Macro"):
            params.append(name)
    return params


def create_device_from_schema(kind):
    """Create a minimal device object using the parameter schema."""
    schema = load_effect_schema(kind)
    params = {}
    for name, info in schema.items():
        if name.startswith("Macro"):
            continue
        if name == "Enabled":
            params[name] = True
            continue
        t = info.get("type")
        if t == "number":
            params[name] = info.get("min", 0.0)
        elif t == "boolean":
            params[name] = False
        elif t == "enum":
            opts = info.get("options")
            params[name] = opts[0] if opts else ""
        else:
            params[name] = 0
    return {"kind": kind, "name": kind, "parameters": params}


def create_effect_rack(device_kinds, macro_map, output_path, name="Effect Rack"):
    """Create an audio effect rack preset from device kinds."""
    try:
        devices = [create_device_from_schema(k) for k in device_kinds]
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
