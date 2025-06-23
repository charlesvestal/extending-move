#!/usr/bin/env python3
"""Utilities for building Audio Effect Rack chains."""

import os
import json
import logging
from core.refresh_handler import refresh_library

logger = logging.getLogger(__name__)

# Map effect kinds to example preset paths used for extracting parameters
DEFAULT_EFFECT_PRESETS = {
    "autoFilter": os.path.join("examples", "Audio Effects", "Auto Filter", "Default Filter.json"),
    "reverb": os.path.join("examples", "Audio Effects", "Reverb", "Default Reverb.json"),
    "redux2": os.path.join("examples", "Audio Effects", "Redux", "Default Redux.json"),
    "phaser": os.path.join("examples", "Audio Effects", "Phaser-Flanger", "Phaser Default.json"),
    "delay": os.path.join("examples", "Audio Effects", "Delay", "Time Delay.json"),
    "compressor": os.path.join("examples", "Audio Effects", "Dynamics", "Fast.json"),
    "chorus": os.path.join("examples", "Audio Effects", "Chorus-Ensemble", "Chorus Default.json"),
    "channelEq": os.path.join("examples", "Audio Effects", "Channel EQ", "Default EQ.json"),
    "saturator": os.path.join("examples", "Audio Effects", "Saturator", "Default Saturator.json"),
}

USER_FX_DIR = os.path.join("/data/UserData/UserLibrary/Audio Effects")


def get_effect_parameters(effect_kind):
    """Return the parameter names for the given effect kind."""
    preset = DEFAULT_EFFECT_PRESETS.get(effect_kind)
    if not preset or not os.path.exists(preset):
        return []
    try:
        with open(preset, "r") as f:
            data = json.load(f)
        params = data.get("parameters", {})
        return sorted(params.keys())
    except Exception as exc:
        logger.warning("Failed to read preset %s: %s", preset, exc)
        return []


def create_fx_chain(effect_kinds, knob_map, preset_name):
    """Create an Audio Effect Rack preset.

    Args:
        effect_kinds: List of effect names (strings). Up to four entries.
        knob_map: Mapping of macro index to {"effect_index": int, "parameter": str}
        preset_name: Name of the new preset (with or without extension).

    Returns:
        dict with success, message, path.
    """
    try:
        devices = []
        for kind in effect_kinds:
            if not kind:
                continue
            preset = DEFAULT_EFFECT_PRESETS.get(kind)
            if not preset or not os.path.exists(preset):
                continue
            with open(preset, "r") as f:
                data = json.load(f)
            dev = {
                "presetUri": None,
                "kind": kind,
                "name": "",
                "parameters": data.get("parameters", {}),
                "deviceData": data.get("deviceData", {}),
            }
            devices.append(dev)

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
                    "mixer": {"pan": 0.0, "solo-cue": False, "speakerOn": True, "volume": 0.0, "sends": []},
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
                rack["parameters"][f"Macro{macro_idx}"] = {"value": val["value"], "customName": param}
            else:
                params[param] = {
                    "value": val,
                    "macroMapping": {
                        "macroIndex": macro_idx,
                        "rangeMin": 0.0,
                        "rangeMax": 1.0,
                    },
                }
                rack["parameters"][f"Macro{macro_idx}"] = {"value": val, "customName": param}

        os.makedirs(USER_FX_DIR, exist_ok=True)
        if not preset_name.endswith(".ablpreset") and not preset_name.endswith(".json"):
            preset_name += ".ablpreset"
        dest = os.path.join(USER_FX_DIR, preset_name)
        with open(dest, "w") as f:
            json.dump(rack, f, indent=2)
            f.write("\n")
        refresh_library()
        return {"success": True, "message": f"Created preset {preset_name}", "path": dest}
    except Exception as exc:
        logger.error("FX chain creation failed: %s", exc)
        return {"success": False, "message": f"Error creating FX chain: {exc}"}
