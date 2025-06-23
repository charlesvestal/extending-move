#!/usr/bin/env python3
"""Utilities for working with audio effect chain presets."""
import json
import os
import shutil
import logging

from .synth_preset_inspector_handler import (
    update_preset_parameter_mappings,
    update_preset_macro_names,
    extract_macro_information,
)

logger = logging.getLogger(__name__)


def extract_effect_parameters(preset_path):
    """Return parameter names and paths for all devices in an effect preset."""
    try:
        with open(preset_path, "r") as f:
            preset_data = json.load(f)

        params = []

        def walk(data, path=""):
            if isinstance(data, dict):
                if path.endswith("parameters"):
                    for k in data.keys():
                        if k != "Enabled" and not k.startswith("Macro"):
                            params.append({"name": k, "path": f"{path}.{k}"})
                for key, val in data.items():
                    new = f"{path}.{key}" if path else key
                    walk(val, new)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    walk(item, f"{path}[{i}]")

        walk(preset_data)
        return {
            "success": True,
            "message": f"Found {len(params)} parameters",
            "parameters": params,
        }
    except Exception as exc:
        logger.error("Parameter extraction failed: %s", exc)
        return {"success": False, "message": f"Error extracting parameters: {exc}", "parameters": []}


def apply_macro_mappings(preset_path, macro_data, output_path=None, name_updates=None):
    """Apply macro mappings and optional names to an effect preset."""
    try:
        dest = output_path or preset_path
        if output_path:
            shutil.copy(preset_path, dest)
            preset_path = dest

        result = update_preset_parameter_mappings(preset_path, macro_data)
        if not result["success"]:
            return result

        if name_updates:
            name_result = update_preset_macro_names(preset_path, name_updates)
            if not name_result["success"]:
                return name_result

        return {"success": True, "message": result["message"], "path": dest}
    except Exception as exc:
        logger.error("Macro mapping failed: %s", exc)
        return {"success": False, "message": f"Error applying macro mappings: {exc}"}

