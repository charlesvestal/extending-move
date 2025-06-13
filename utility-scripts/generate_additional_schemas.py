import json
import glob
import collections
from genson import SchemaBuilder


def generate_drumrack_schema(preset_paths, out_path):
    params = collections.defaultdict(lambda: {"type": None, "min": None, "max": None, "options": set()})

    def update(name, value):
        entry = params[name]
        if isinstance(value, bool):
            entry["type"] = "boolean"
        elif isinstance(value, (int, float)):
            entry["type"] = "number"
            entry["min"] = value if entry["min"] is None else min(entry["min"], value)
            entry["max"] = value if entry["max"] is None else max(entry["max"], value)
        elif isinstance(value, str):
            if entry["type"] not in ("enum", "string"):
                entry["type"] = "enum"
            entry["options"].add(value)

    def traverse(obj):
        if isinstance(obj, dict):
            if obj.get("kind") == "drumCell":
                for k, v in obj.get("parameters", {}).items():
                    update(k, v)
            for v in obj.values():
                traverse(v)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    for path in preset_paths:
        with open(path) as f:
            traverse(json.load(f))

    schema = {}
    for name, info in sorted(params.items()):
        if info["type"] == "enum":
            schema[name] = {"type": "enum", "options": sorted(info["options"])}
        elif info["type"] == "boolean":
            schema[name] = {"type": "boolean", "options": []}
        else:
            schema[name] = {"type": "number", "min": info["min"], "max": info["max"], "options": []}

    with open(out_path, "w") as f:
        json.dump(schema, f, indent=2)
    return len(schema)


def generate_set_schema(set_paths, out_path):
    builder = SchemaBuilder()
    for path in set_paths:
        with open(path) as f:
            builder.add_object(json.load(f))
    with open(out_path, "w") as f:
        json.dump(builder.to_schema(), f, indent=2)


def main():
    drum_paths = glob.glob('examples/Track Presets/drumRack/*.json')
    set_paths = glob.glob('examples/Sets/*.abl')
    drum_count = generate_drumrack_schema(drum_paths, 'static/schemas/drumRack_schema.json')
    generate_set_schema(set_paths, 'static/schemas/abl_set_schema.json')
    print(f'Generated drumRack schema with {drum_count} parameters')
    print('Generated set schema from', len(set_paths), 'example sets')


if __name__ == '__main__':
    main()
