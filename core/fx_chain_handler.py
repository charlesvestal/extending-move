import json
import logging
from typing import Any, Dict, List

from .fx_browser_handler import load_fx_chain_schema
from .synth_preset_inspector_handler import (
    update_preset_parameter_mappings,
)
from .synth_param_editor_handler import update_macro_values


def update_fx_parameters(
    preset_path: str, param_updates: Dict[str, str], output_path: str | None = None
) -> Dict[str, Any]:
    """Update parameter values in an effect or FX chain preset."""
    try:
        with open(preset_path, "r") as f:
            preset_data = json.load(f)

        info = extract_fx_parameters(preset_path)
        if not info["success"]:
            return info
        paths = info.get("parameter_paths", {})

        def get_parent_and_key(data: Any, path: str):
            parts = path.split(".")
            current = data
            for part in parts[:-1]:
                if part.endswith("]") and "[" in part:
                    name, idx = part[:-1].split("[")
                    if name:
                        current = current.get(name, [])
                    idx = int(idx)
                    if not isinstance(current, list) or idx >= len(current):
                        return None, None
                    current = current[idx]
                else:
                    current = current.get(part)
                    if current is None:
                        return None, None
            return current, parts[-1]

        def cast_value(val_str: str, original: Any) -> Any:
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
                orig = target["value"]
                target["value"] = cast_value(val, orig)
            else:
                orig = target
                parent[key] = cast_value(val, orig)
            updated += 1

        dest = output_path or preset_path
        with open(dest, "w") as f:
            json.dump(preset_data, f, indent=2)
            f.write("\n")

        return {"success": True, "message": f"Updated {updated} parameters", "path": dest}
    except Exception as exc:
        logger.error("FX parameter update failed: %s", exc)
        return {"success": False, "message": f"Error updating parameters: {exc}"}

logger = logging.getLogger(__name__)

IGNORED_PARAMS = {"lockId", "lockSeal"}


def build_fx_chain_from_preset(preset_path: str) -> Dict[str, Any]:
    """Return an FX chain preset from ``preset_path``.

    If the preset is a single effect, wrap it in the default FX chain schema.
    """
    with open(preset_path, "r") as f:
        data = json.load(f)

    if data.get("kind") == "audioEffectRack":
        return data

    chain = load_fx_chain_schema()
    if chain.get("chains"):
        chain["chains"][0]["devices"] = [data]
    return chain


def extract_fx_parameters(preset_path: str) -> Dict[str, Any]:
    """Return parameter names, values and paths from an effect or chain."""
    try:
        with open(preset_path, "r") as f:
            data = json.load(f)

        params: List[Dict[str, Any]] = []
        paths: Dict[str, str] = {}

        def walk(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                if path.endswith("parameters"):
                    for key, val in obj.items():
                        if key in IGNORED_PARAMS or key.startswith("Macro"):
                            continue
                        value = val.get("value") if isinstance(val, dict) else val
                        params.append({"name": key, "value": value})
                        paths.setdefault(key, f"{path}.{key}")
                for k, v in obj.items():
                    walk(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    walk(item, f"{path}[{i}]")

        walk(data)

        return {
            "success": True,
            "parameters": params,
            "parameter_paths": paths,
            "message": f"Found {len(params)} parameters",
        }
    except Exception as exc:
        logger.error("Error extracting FX parameters: %s", exc)
        return {"success": False, "message": f"Error: {exc}", "parameters": []}


def save_fx_chain_with_macros(
    source_preset: str,
    macros: List[Dict[str, Any]],
    dest_path: str,
    param_updates: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Create an FX chain from ``source_preset`` with macro assignments.

    ``param_updates`` may contain parameter values to update in the resulting
    chain.
    """
    try:
        with open(source_preset, "r") as f:
            source_data = json.load(f)

        is_chain = source_data.get("kind") == "audioEffectRack"

        chain = source_data if is_chain else build_fx_chain_from_preset(source_preset)
        with open(dest_path, "w") as f:
            json.dump(chain, f, indent=2)
            f.write("\n")

        name_updates: Dict[int, str] = {}
        value_updates: Dict[int, str] = {}
        for m in macros:
            idx = int(m.get("index", 0))
            if "name" in m:
                name_updates[idx] = m.get("name", "")
            if "value" in m:
                value_updates[idx] = str(m["value"])
            for p in m.get("parameters", []):
                p_path = p.get("path")
                if not is_chain and p_path:
                    p_path = f"chains[0].devices[0].{p_path}"
                upd = {
                    idx: {
                        "parameter_path": p_path,
                        "rangeMin": p.get("rangeMin"),
                        "rangeMax": p.get("rangeMax"),
                    }
                }
                res = update_preset_parameter_mappings(dest_path, upd)
                if not res["success"]:
                    return res

        if name_updates:
            try:
                with open(dest_path, "r") as f:
                    chain_data = json.load(f)
                for n_idx, n_val in name_updates.items():
                    macro_key = f"Macro{n_idx}"
                    if macro_key in chain_data.get("parameters", {}):
                        param = chain_data["parameters"][macro_key]
                        if isinstance(param, dict):
                            if n_val:
                                param["customName"] = n_val
                            else:
                                param.pop("customName", None)
                        else:
                            if n_val:
                                chain_data["parameters"][macro_key] = {
                                    "value": param,
                                    "customName": n_val,
                                }
                with open(dest_path, "w") as f:
                    json.dump(chain_data, f, indent=2)
                    f.write("\n")
            except Exception as exc:
                return {"success": False, "message": f"Error updating macro names: {exc}"}
        if value_updates:
            res = update_macro_values(dest_path, value_updates, dest_path)
            if not res["success"]:
                return res
        if param_updates:
            res = update_fx_parameters(dest_path, param_updates, dest_path)
            if not res["success"]:
                return res
        return {"success": True, "path": dest_path, "message": "Saved FX chain"}
    except Exception as exc:
        logger.error("Failed to save FX chain: %s", exc)
        return {"success": False, "message": f"Error saving chain: {exc}"}
