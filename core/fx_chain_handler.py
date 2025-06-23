#!/usr/bin/env python3
"""Utilities for working with audio effect chains."""
import json
import os
import logging

logger = logging.getLogger(__name__)

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'schemas')


def load_schema(kind):
    """Load parameter schema for the given effect kind."""
    path = os.path.join(SCHEMA_DIR, f'{kind}_schema.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as exc:
        logger.warning('Could not load schema %s: %s', path, exc)
        return {}


def parse_chain(preset_path):
    """Return effects and macro mapping info from an audio effect preset."""
    try:
        with open(preset_path, 'r') as f:
            data = json.load(f)
    except Exception as exc:
        return {'success': False, 'message': f'Error reading preset: {exc}'}

    effects = []
    macros = {}
    name = data.get('name', '')

    if data.get('kind') == 'audioEffectRack':
        chains = data.get('chains', [])
        if chains:
            chain = chains[0]
            for idx, dev in enumerate(chain.get('devices', [])):
                params = dev.get('parameters', {})
                effects.append({'kind': dev.get('kind'), 'parameters': params})
                for p_name, val in params.items():
                    if isinstance(val, dict) and 'macroMapping' in val:
                        m = val['macroMapping'].get('macroIndex')
                        macros[m] = {'effect_index': idx, 'param': p_name}
    else:
        effects.append({'kind': data.get('kind'), 'parameters': data.get('parameters', {})})

    return {
        'success': True,
        'name': name,
        'effects': effects,
        'macros': macros,
    }


def create_chain(name, effects, macros, output_path):
    """Create a chain preset from effect data and macro mapping."""
    chain = {
        "$schema": "http://tech.ableton.com/schema/song/1.5.1/devicePreset.json",
        "kind": "audioEffectRack",
        "name": name,
        "parameters": {"Enabled": True},
        "chains": [
            {
                "name": "",
                "color": 0,
                "devices": [],
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
        chain["parameters"][f"Macro{i}"] = 0.0

    dev_list = chain["chains"][0]["devices"]

    for eff in effects:
        dev = {
            "presetUri": None,
            "kind": eff["kind"],
            "name": "",
            "parameters": eff.get("parameters", {}),
            "deviceData": {},
        }
        dev_list.append(dev)

    for macro_idx, mapping in macros.items():
        e_idx = mapping["effect_index"]
        param = mapping["param"]
        if e_idx >= len(dev_list):
            continue
        dev = dev_list[e_idx]
        val = dev["parameters"].get(param)
        if val is None:
            continue
        if isinstance(val, dict):
            cur_val = val.get("value")
        else:
            cur_val = val
        schema = load_schema(dev["kind"]).get(param, {})
        min_v = schema.get("min", 0.0)
        max_v = schema.get("max", 1.0)
        dev["parameters"][param] = {
            "value": cur_val,
            "macroMapping": {"macroIndex": int(macro_idx), "rangeMin": min_v, "rangeMax": max_v},
        }

    try:
        with open(output_path, 'w') as f:
            json.dump(chain, f, indent=2)
            f.write('\n')
        return {"success": True, "path": output_path, "message": "Chain saved"}
    except Exception as exc:
        return {"success": False, "message": f"Error writing preset: {exc}"}
