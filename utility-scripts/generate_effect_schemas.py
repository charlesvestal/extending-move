import json
import glob
import collections
from decimal import Decimal

OUTPUT_DIR = 'static/schemas'
SAMPLE_GLOB = 'examples/Audio Effects/*/*.json'


def count_decimals(value):
    d = Decimal(str(value)).normalize()
    return abs(d.as_tuple().exponent) if d.as_tuple().exponent < 0 else 0


def update_param(entry, value):
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


def traverse(obj, kind_params):
    if isinstance(obj, dict):
        kind = obj.get('kind')
        if kind and 'parameters' in obj:
            params = kind_params[kind]
            for name, val in obj['parameters'].items():
                if isinstance(val, dict) and 'value' in val:
                    val = val['value']
                entry = params.setdefault(name, {'type': None, 'min': None, 'max': None})
                update_param(entry, val)
        for v in obj.values():
            traverse(v, kind_params)
    elif isinstance(obj, list):
        for item in obj:
            traverse(item, kind_params)


def build_schemas(paths):
    kind_params = collections.defaultdict(dict)
    for path in paths:
        with open(path) as f:
            traverse(json.load(f), kind_params)
    schemas = {}
    for kind, params in kind_params.items():
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
        schemas[kind] = schema
    return schemas


def main():
    paths = glob.glob(SAMPLE_GLOB)
    schemas = build_schemas(paths)
    for kind, schema in schemas.items():
        out_path = f"{OUTPUT_DIR}/{kind}_schema.json"
        with open(out_path, 'w') as f:
            json.dump(schema, f, indent=2)
        print(f"Generated {kind} schema with {len(schema)} parameters")


if __name__ == '__main__':
    main()
