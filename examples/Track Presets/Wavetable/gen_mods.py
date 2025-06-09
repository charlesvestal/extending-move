#!/usr/bin/env python3
import json
import copy
import sys
import os

# zero-based list of modulation source names
SOURCE_NAMES = [
    "Amp Envelope",
    "Envelope 2",
    "Envelope 3",
    "LFO 1",
    "LFO 2",
    "Time",
    "Amount",
    "Velocity",
    "Key",
    "Pitch Bend",
    "Aftertouch",
    "Mod Wheel",
    "Random"
]

def find_wavetable_devices(obj):
    """
    Recursively walk obj and return a list of any dict where obj['kind']=='wavetable'.
    """
    matches = []
    if isinstance(obj, dict):
        if obj.get("kind") == "wavetable":
            matches.append(obj)
        for v in obj.values():
            matches.extend(find_wavetable_devices(v))
    elif isinstance(obj, list):
        for item in obj:
            matches.extend(find_wavetable_devices(item))
    return matches

def main(template_path="Template.json"):
    # load the blank template
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    # for each index/source, clone + patch + write
    for idx, src_name in enumerate(SOURCE_NAMES):
        preset = copy.deepcopy(template)

        # 1) rename top-level preset name
        preset["name"] = f"{idx} – {src_name}"

        # 2) find every wavetable device and inject our modulation array
        #    now inject into Voice_Global_PitchModulation (the actual pitch-modulation knob)
        wavs = find_wavetable_devices(preset)
        if not wavs:
            sys.exit("Error: no wavetable device found in template.")
        for dev in wavs:
            dd = dev.setdefault("deviceData", {})
            mods = dd.setdefault("modulations", {})
            # 3) build a 13-element float array with 0.5 at idx
            arr = [0.0] * len(SOURCE_NAMES)
            arr[idx] = 0.5
            mods["Voice_Global_PitchModulation"] = arr

        # 4) write out as .ablpreset
        filename = f"{idx} – {src_name}.ablpreset"
        with open(filename, "w", encoding="utf-8") as out:
            json.dump(preset, out, indent=2, ensure_ascii=False)
        print(f"Wrote {filename}")

if __name__ == "__main__":
    # optionally pass a custom template path: python gen_mods.py MyTemplate.json
    tpl = sys.argv[1] if len(sys.argv) > 1 else "Template.json"
    main(tpl)