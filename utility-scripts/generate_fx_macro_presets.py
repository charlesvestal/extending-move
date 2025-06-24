import os
import re
import sys
from typing import Dict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.fx_chain_handler import extract_fx_parameters, save_fx_chain_with_macros

AUDIO_EFFECTS_DIR = os.path.join('examples', 'Audio Effects')
OUTPUT_ROOT = os.path.join('examples', 'FX Macro Presets')


def sanitize_filename(name: str) -> str:
    """Return a safe filename component."""
    name = re.sub(r"[\\/:]+", '-', name)
    name = name.replace(' ', '_')
    return name


def find_base_preset(effect_dir: str) -> str:
    """Return a preset path to use as the base for an effect."""
    for f in os.listdir(effect_dir):
        if f.lower().startswith('default') and f.endswith('.json'):
            return os.path.join(effect_dir, f)
    for f in os.listdir(effect_dir):
        if f.endswith('.json'):
            return os.path.join(effect_dir, f)
    return ''


def generate_presets_for_effect(effect_name: str, preset_path: str) -> int:
    """Generate macro presets for a single effect."""
    info = extract_fx_parameters(preset_path)
    if not info.get('success'):
        print(f"Failed to read {preset_path}: {info.get('message')}")
        return 0
    params = info.get('parameters', [])
    paths: Dict[str, str] = info.get('parameter_paths', {})

    out_dir = os.path.join(OUTPUT_ROOT, effect_name)
    os.makedirs(out_dir, exist_ok=True)

    count = 0
    for i, param in enumerate(params, 1):
        name = param['name']
        path = paths.get(name)
        if not path:
            continue
        macros = [{
            'index': 0,
            'name': name,
            'parameters': [{
                'name': name,
                'path': path,
            }]
        }]
        filename = f"{effect_name} - {i:03d} - {sanitize_filename(name)}.ablpreset"
        dest = os.path.join(out_dir, filename)
        res = save_fx_chain_with_macros(preset_path, macros, dest)
        if res.get('success'):
            count += 1
        else:
            print(f"Error saving {filename}: {res.get('message')}")
    return count


def main() -> None:
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    total = 0
    for effect in sorted(os.listdir(AUDIO_EFFECTS_DIR)):
        effect_path = os.path.join(AUDIO_EFFECTS_DIR, effect)
        if not os.path.isdir(effect_path):
            continue
        base = find_base_preset(effect_path)
        if not base:
            print(f"No preset found for {effect}")
            continue
        print(f"Processing {effect} using {os.path.basename(base)}")
        count = generate_presets_for_effect(effect, base)
        print(f"  created {count} presets")
        total += count
    print(f"Generated {total} preset files in {OUTPUT_ROOT}")


if __name__ == '__main__':
    main()
