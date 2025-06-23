#!/usr/bin/env python3
"""Utilities for creating Audio Effect Rack presets."""

import os
import json
import logging
from typing import Dict, List

from core.refresh_handler import refresh_library

logger = logging.getLogger(__name__)

CORE_FX_DIR = "/data/CoreLibrary/Audio Effects"
USER_FX_DIR = "/data/UserData/UserLibrary/Audio Effects"


def load_fx_presets(base_dir: str = CORE_FX_DIR) -> Dict[str, Dict[str, dict]]:
    """Scan the Core Library and load all effect presets with parameters."""
    presets: Dict[str, Dict[str, dict]] = {}
    if not os.path.exists(base_dir):
        return presets

    for root, _dirs, files in os.walk(base_dir):
        kind = os.path.basename(root)
        for file in files:
            if not file.endswith((".json", ".ablpreset")):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                params = data.get("parameters", {})
                presets.setdefault(kind, {})[os.path.splitext(file)[0]] = {
                    "path": path,
                    "parameters": {
                        k: (v.get("value") if isinstance(v, dict) else v)
                        for k, v in params.items()
                    },
                    "kind": data.get("kind", kind),
                    "deviceData": data.get("deviceData", {}),
                }
            except Exception as exc:
                logger.warning("Failed to load preset %s: %s", path, exc)
    return presets


def create_fx_chain(
    preset_paths: List[str],
    knob_map: Dict[int, Dict[str, str]],
    preset_name: str,
    param_values: Dict[int, Dict[str, str]] | None = None,
) -> Dict[str, object]:
    """Create an Audio Effect Rack preset from selected effect presets."""

    param_values = param_values or {}
    try:
        devices = []
        for idx, path in enumerate(preset_paths):
            if not path:
                continue
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            params = data.get("parameters", {})
            for key, val in param_values.get(idx, {}).items():
                if key in params:
                    if isinstance(params[key], dict) and "value" in params[key]:
                        params[key]["value"] = val
                    else:
                        params[key] = val
                else:
                    params[key] = val
            devices.append(
                {
                    "presetUri": None,
                    "kind": data.get("kind"),
                    "name": data.get("name", ""),
                    "parameters": params,
                    "deviceData": data.get("deviceData", {}),
                }
            )

        rack = {
            "$schema": "http://tech.ableton.com/schema/song/1.5.1/devicePreset.json",
            "kind": "audioEffectRack",
            "name": preset_name,
            "parameters": {"Enabled": True},
            "chains": [
                {
                    "name": "",
                    "color": 0,
                    "devices": devices,
                    "mixer": {
                        "pan": 0.0,
                        "solo-cue": False,
                        "speakerOn": True,
                        "volume": 0.0,
                        "sends": [],
                    },
                }
            ],
        }

        for i in range(8):
            rack["parameters"][f"Macro{i}"] = 0.0

        for macro_idx, mapping in knob_map.items():
            eff_idx = mapping.get("effect_index")
            param = mapping.get("parameter")
            if eff_idx is None or param is None:
                continue
            if eff_idx < 0 or eff_idx >= len(devices):
                continue
            dev = devices[eff_idx]
            params = dev.get("parameters", {})
            if param not in params:
                continue
            val = params[param]
            if isinstance(val, dict) and "value" in val:
                params[param]["macroMapping"] = {
                    "macroIndex": macro_idx,
                    "rangeMin": 0.0,
                    "rangeMax": 1.0,
                }
                rack["parameters"][f"Macro{macro_idx}"] = {
                    "value": val["value"],
                    "customName": param,
                }
            else:
                params[param] = {
                    "value": val,
                    "macroMapping": {
                        "macroIndex": macro_idx,
                        "rangeMin": 0.0,
                        "rangeMax": 1.0,
                    },
                }
                rack["parameters"][f"Macro{macro_idx}"] = {
                    "value": val,
                    "customName": param,
                }

        os.makedirs(USER_FX_DIR, exist_ok=True)
        if not preset_name.endswith(".ablpreset") and not preset_name.endswith(".json"):
            preset_name += ".ablpreset"
        dest = os.path.join(USER_FX_DIR, preset_name)
        with open(dest, "w") as f:
            json.dump(rack, f, indent=2)
            f.write("\n")
        refresh_library()
        return {
            "success": True,
            "message": f"Created preset {preset_name}",
            "path": dest,
        }
    except Exception as exc:
        logger.error("FX chain creation failed: %s", exc)
        return {"success": False, "message": f"Error creating FX chain: {exc}"}
