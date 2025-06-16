#!/usr/bin/env python3
"""Core logic for editing synth preset parameter values."""
import os
import json
import logging

from .synth_preset_inspector_handler import extract_available_parameters

logger = logging.getLogger(__name__)


def update_parameter_values(
    preset_path,
    param_updates,
    output_path=None,
    device_types=("drift",),
):
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

        info = extract_available_parameters(preset_path, device_types=device_types)
        if not info["success"]:
            return info
        paths = info.get("parameter_paths", {})

        def get_parent_and_key(data, path):
            parts = path.split(".")
            current = data
            for part in parts[:-1]:
                if "[" in part and part.endswith("]"):
                    name, idx = part[:-1].split("[")
                    if name:
                        current = current.get(name, [])
                    else:
                        pass
                    idx = int(idx)
                    if not isinstance(current, list) or idx >= len(current):
                        return None, None
                    current = current[idx]
                else:
                    current = current.get(part)
                    if current is None:
                        return None, None
            return current, parts[-1]

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
        macro_updates: Mapping of macro index to update info. Each value can
            be either the new value directly or a dict with keys:
            - value: new macro value
            - path: optional path to the macro parameter
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

        def update_macros(obj, cur_path=""):
            nonlocal updated
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if key.startswith("Macro") and key[5:].isdigit():
                        idx = int(key[5:])
                        upd = macro_updates.get(idx)
                        macro_path = f"{cur_path}.{key}" if cur_path else key
                        if isinstance(upd, dict):
                            target_val = upd.get("value")
                            target_path = upd.get("path")
                            if target_path and target_path != macro_path:
                                # Not the macro we want to update
                                pass
                            else:
                                if isinstance(val, dict) and "value" in val:
                                    val["value"] = cast_value(target_val, val["value"])
                                else:
                                    obj[key] = cast_value(target_val, val)
                                updated += 1
                        elif upd is not None:
                            if isinstance(val, dict) and "value" in val:
                                val["value"] = cast_value(upd, val["value"])
                            else:
                                obj[key] = cast_value(upd, val)
                            updated += 1
                    update_macros(val, f"{cur_path}.{key}" if cur_path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    update_macros(item, f"{cur_path}[{i}]")

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

