import json
import glob
import collections
from decimal import Decimal

# Mapping of instrument kind to output schema file
INSTRUMENT_SCHEMAS = {
    'drift': 'static/schemas/drift_schema.json',
    'wavetable': 'static/schemas/wavetable_schema.json',
    'melodicSampler': 'static/schemas/melodicSampler_schema.json',
}


def count_decimals(value):
    """Return number of decimal digits for a numeric value."""
    d = Decimal(str(value)).normalize()
    return abs(d.as_tuple().exponent) if d.as_tuple().exponent < 0 else 0


def update_param(entry, value):
    """Update schema entry based on the observed value."""
    if isinstance(value, bool):
        entry['type'] = 'boolean'
    elif isinstance(value, (int, float)):
        entry['type'] = 'number'
        entry['min'] = value if entry['min'] is None else min(entry['min'], value)
        entry['max'] = value if entry['max'] is None else max(entry['max'], value)
        dec = min(count_decimals(value), 4)
        entry['decimals'] = max(entry.get('decimals', 0), dec)
    elif isinstance(value, str):
        if entry['type'] not in ('enum', 'string'):
            entry['type'] = 'enum'
        entry.setdefault('options', set()).add(value)


def traverse(obj, kind, params):
    """Recursively search for instrument parameters."""
    if isinstance(obj, dict):
        if obj.get('kind') == kind:
            for name, val in obj.get('parameters', {}).items():
                if isinstance(val, dict) and 'value' in val:
                    val = val['value']
                entry = params.setdefault(name, {'type': None, 'min': None, 'max': None})
                update_param(entry, val)
        for v in obj.values():
            traverse(v, kind, params)
    elif isinstance(obj, list):
        for item in obj:
            traverse(item, kind, params)


def build_schema(kind, preset_paths):
    params = {}
    for path in preset_paths:
        with open(path) as f:
            data = json.load(f)
        traverse(data, kind, params)

    schema = {}
    for name, info in sorted(params.items()):
        entry = {'type': info['type'], 'options': []}
        if info['type'] == 'number':
            entry['min'] = info['min']
            entry['max'] = info['max']
            if info.get('decimals'):
                entry['decimals'] = info['decimals']
        elif info['type'] == 'enum':
            entry['options'] = sorted(info['options'])
        schema[name] = entry
    return schema


def main():
    paths = glob.glob('examples/CoreLibrary/**/*.json', recursive=True)
    for kind, out_path in INSTRUMENT_SCHEMAS.items():
        schema = build_schema(kind, paths)
        with open(out_path, 'w') as f:
            json.dump(schema, f, indent=2)
        print(f'Generated {kind} schema with {len(schema)} parameters')


if __name__ == '__main__':
    main()
