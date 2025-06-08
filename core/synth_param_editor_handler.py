#!/usr/bin/env python3
"""Core logic for editing synth preset parameter values."""
import os
import json
import logging

from .synth_preset_inspector_handler import extract_available_parameters
from .json_utils import get_parent_and_key

logger = logging.getLogger(__name__)


def update_parameter_values(preset_path, param_updates, output_path=None):
    """Update parameter values in a preset.

    Args:
        preset_path: Path to the source preset.
        param_updates: Mapping of parameter name to new value (as strings).
        output_path: Optional path for the modified preset. If omitted, the
            source preset is overwritten.

    Returns:
        dict with keys:
            - success: bool
            - message: status or error message
            - path: path to written preset
    """
    try:
        with open(preset_path, "r") as f:
            preset_data = json.load(f)

        info = extract_available_parameters(preset_path)
        if not info["success"]:
            return info
        paths = info.get("parameter_paths", {})


        def cast_value(val_str, original):
            """Cast the string ``val_str`` to the same type as ``original``."""
            if isinstance(original, bool):
                try:
                    return bool(int(val_str))
                except ValueError:
                    return original
            if isinstance(original, int) and not isinstance(original, bool):
                try:
                    return int(float(val_str))
                except ValueError:
                    return original
            if isinstance(original, float):
                try:
                    return float(val_str)
                except ValueError:
                    return original
            return val_str

        updated = 0
        for name, val in param_updates.items():
            path = paths.get(name)
            if not path:
                continue
            parent, key = get_parent_and_key(preset_data, path)
            if parent is None or key not in parent:
                continue
            target = parent[key]

            if isinstance(target, dict) and "value" in target:
                orig_val = target["value"]
                target["value"] = cast_value(val, orig_val)
            else:
                orig_val = target
                parent[key] = cast_value(val, orig_val)
            updated += 1

        dest = output_path or preset_path
        with open(dest, "w") as f:
            json.dump(preset_data, f, indent=2)
            f.write("\n")

        return {
            "success": True,
            "message": f"Updated {updated} parameters",
            "path": dest,
        }
    except Exception as exc:
        logger.error("Parameter update failed: %s", exc)
        return {"success": False, "message": f"Error updating parameters: {exc}"}


def update_macro_values(preset_path, macro_updates, output_path=None):
    """Update macro values in a preset.

    Args:
        preset_path: Path to the source preset.
        macro_updates: Mapping of macro index to new value (as strings).
        output_path: Optional path for the modified preset. If omitted, the
            source preset is overwritten.

    Returns:
        dict with keys:
            - success: bool
            - message: status or error message
            - path: path to written preset
    """
    try:
        with open(preset_path, "r") as f:
            preset_data = json.load(f)

        def cast_value(val_str, original):
            if isinstance(original, bool):
                try:
                    return bool(int(val_str))
                except ValueError:
                    return original
            if isinstance(original, int) and not isinstance(original, bool):
                try:
                    return int(float(val_str))
                except ValueError:
                    return original
            if isinstance(original, float):
                try:
                    return float(val_str)
                except ValueError:
                    return original
            return val_str

        updated = 0

        def update_macros(obj):
            nonlocal updated
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if key.startswith("Macro") and key[5:].isdigit():
                        idx = int(key[5:])
                        if idx in macro_updates:
                            new_val = macro_updates[idx]
                            if isinstance(val, dict) and "value" in val:
                                val["value"] = cast_value(new_val, val["value"])
                            else:
                                obj[key] = cast_value(new_val, val)
                            updated += 1
                    update_macros(val)
            elif isinstance(obj, list):
                for item in obj:
                    update_macros(item)

        update_macros(preset_data)

        dest = output_path or preset_path
        with open(dest, "w") as f:
            json.dump(preset_data, f, indent=2)
            f.write("\n")

        return {
            "success": True,
            "message": f"Updated {updated} macro values",
            "path": dest,
        }
    except Exception as exc:
        logger.error("Macro value update failed: %s", exc)
        return {"success": False, "message": f"Error updating macro values: {exc}"}

