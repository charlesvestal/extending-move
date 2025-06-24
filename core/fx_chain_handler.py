import json
import logging
from typing import Any, Dict, List

from .fx_browser_handler import load_fx_chain_schema
from .synth_preset_inspector_handler import (
    update_preset_parameter_mappings,
)
from .synth_param_editor_handler import update_macro_values

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
    """Return parameter information from an effect or chain.

    The result includes a nested ``device`` structure for rendering and a flat
    list of parameters with their JSON paths for macro mapping.
    """
    try:
        with open(preset_path, "r") as f:
            data = json.load(f)

        flat_params: List[Dict[str, Any]] = []
        paths: Dict[str, str] = {}

        def parse_device(dev: Dict[str, Any], base: str = "") -> Dict[str, Any]:
            """Recursively collect parameters and child devices."""
            kind = dev.get("kind", "unknown")
            params: List[Dict[str, Any]] = []

            for key, val in dev.get("parameters", {}).items():
                if key in IGNORED_PARAMS or key.startswith("Macro"):
                    continue
                value = val.get("value") if isinstance(val, dict) else val
                param_path = f"{base}.parameters.{key}" if base else f"parameters.{key}"
                params.append({"name": key, "value": value})
                flat_params.append({"name": key, "value": value})
                paths.setdefault(key, param_path)

            children: List[Dict[str, Any]] = []
            for i, chain in enumerate(dev.get("chains", [])):
                for j, child in enumerate(chain.get("devices", [])):
                    cpath = f"{base}.chains[{i}].devices[{j}]" if base else f"chains[{i}].devices[{j}]"
                    children.append(parse_device(child, cpath))

            for j, child in enumerate(dev.get("devices", [])):
                cpath = f"{base}.devices[{j}]" if base else f"devices[{j}]"
                children.append(parse_device(child, cpath))

            return {"kind": kind, "parameters": params, "children": children}

        device_info = parse_device(data)

        return {
            "success": True,
            "device": device_info,
            "parameters": flat_params,
            "parameter_paths": paths,
            "kind": data.get("kind"),
            "message": f"Found {len(flat_params)} parameters",
        }
    except Exception as exc:
        logger.error("Error extracting FX parameters: %s", exc)
        return {"success": False, "message": f"Error: {exc}", "parameters": []}


def save_fx_chain_with_macros(
    source_preset: str,
    macros: List[Dict[str, Any]],
    dest_path: str,
) -> Dict[str, Any]:
    """Create an FX chain from ``source_preset`` with macro assignments."""
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
        return {"success": True, "path": dest_path, "message": "Saved FX chain"}
    except Exception as exc:
        logger.error("Failed to save FX chain: %s", exc)
        return {"success": False, "message": f"Error saving chain: {exc}"}
