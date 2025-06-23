import os
import json
from typing import Any, Dict, List

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'schemas')
AUDIO_EFFECTS_SCHEMA_PATH = os.path.join(SCHEMA_DIR, 'audio_effects_schemas.json')
FX_CHAIN_SCHEMA_PATH = os.path.join(SCHEMA_DIR, 'fx_chain_schema.json')


def load_audio_effects_schema() -> Dict[str, Any]:
    """Load metadata for audio effects."""
    try:
        with open(AUDIO_EFFECTS_SCHEMA_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def load_fx_chain_schema() -> Dict[str, Any]:
    """Load the default FX chain schema."""
    try:
        with open(FX_CHAIN_SCHEMA_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


IGNORED_PARAMS = {'lockId', 'lockSeal'}


def _parse_device(device: Dict[str, Any]) -> Dict[str, Any]:
    """Return a simplified dict with parameters and child devices."""
    kind = device.get('kind', 'unknown')
    params: Dict[str, Any] = {}
    for key, val in device.get('parameters', {}).items():
        if key in IGNORED_PARAMS:
            continue
        if isinstance(val, dict) and 'value' in val:
            params[key] = val['value']
        else:
            params[key] = val
    children: List[Dict[str, Any]] = []
    for chain in device.get('chains', []):
        for dev in chain.get('devices', []):
            children.append(_parse_device(dev))
    for dev in device.get('devices', []):
        children.append(_parse_device(dev))
    return {'kind': kind, 'parameters': params, 'children': children}


def extract_fx_parameters(preset_path: str) -> Dict[str, Any]:
    """Load an audio effect or chain preset and return parameter info."""
    try:
        with open(preset_path, 'r') as f:
            data = json.load(f)
        device = _parse_device(data)
        return {'success': True, 'device': device, 'message': 'Parsed preset'}
    except Exception as exc:
        return {'success': False, 'message': f'Error reading preset: {exc}'}
