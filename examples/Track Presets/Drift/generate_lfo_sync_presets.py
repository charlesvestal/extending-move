#!/usr/bin/env python3
"""Generate Drift presets for testing LFO sync rates.

Each preset routes LFO1 to pitch at full amount, removes all macro mappings, and sets both envelope releases to maximum so the modulation can be heard. Files are named by the LFO sync rate.
"""

import json
import copy
import os
import sys


def find_drift_devices(obj):
    """Recursively yield all drift devices in ``obj``."""
    if isinstance(obj, dict):
        if obj.get("kind") == "drift":
            yield obj
        for val in obj.values():
            yield from find_drift_devices(val)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_drift_devices(item)


def remove_macro_mappings(obj):
    """Remove any existing macroMapping entries from ``obj``."""
    if isinstance(obj, dict):
        obj.pop("macroMapping", None)
        for val in obj.values():
            remove_macro_mappings(val)
    elif isinstance(obj, list):
        for item in obj:
            remove_macro_mappings(item)


def main(template_path="Analog Shape - Core.json", out_dir="lfo_sync_test"):
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    os.makedirs(out_dir, exist_ok=True)

    for rate in range(33):  # 0-32 inclusive
        preset = copy.deepcopy(template)
        remove_macro_mappings(preset)

        for dev in find_drift_devices(preset):
            params = dev.setdefault("parameters", {})
            # Ensure LFO pitch modulation
            params["PitchModulation_Source2"] = "LFO"
            params["PitchModulation_Amount2"] = 1.0
            # Set LFO to sync mode and desired rate
            params["Lfo_Mode"] = "Sync"
            params["Lfo_SyncedRate"] = rate
            # Max out envelope releases so the modulation is audible
            params["Envelope1_Release"] = 20.0
            params["Envelope2_Release"] = 20.0
        preset["name"] = f"LFO Sync Rate {rate}"
        filename = os.path.join(out_dir, f"lfo_rate_{rate:02d}.ablpreset")
        with open(filename, "w", encoding="utf-8") as out:
            json.dump(preset, out, indent=2, ensure_ascii=False)
            out.write("\n")
        print(f"Wrote {filename}")


if __name__ == "__main__":
    tpl = sys.argv[1] if len(sys.argv) > 1 else "Analog Shape - Core.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "lfo_sync_test"
    main(tpl, out)

