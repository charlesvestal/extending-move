#!/usr/bin/env python3
"""Core logic for editing synth preset parameter values."""
import os
import json
import logging

from .synth_preset_inspector_handler import extract_available_parameters

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

        updated = 0
        for name, val in param_updates.items():
            path = paths.get(name)
            if not path:
                continue
            parent, key = get_parent_and_key(preset_data, path)
            if parent is None or key not in parent:
                continue
            target = parent[key]
            # Determine numeric vs string
            if isinstance(target, dict) and "value" in target:
                orig_val = target["value"]
                if isinstance(orig_val, (int, float)):
                    try:
                        target["value"] = float(val)
                    except ValueError:
                        continue
                else:
                    target["value"] = val
            else:
                orig_val = target
                if isinstance(orig_val, (int, float)):
                    try:
                        parent[key] = float(val)
                    except ValueError:
                        continue
                else:
                    parent[key] = val
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

