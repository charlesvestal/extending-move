#!/usr/bin/env python3
import sys
import json
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the function we want to test
from core.synth_preset_inspector_handler import update_preset_macro_names

# Create a test preset file
test_preset = {
    "$schema": "http://tech.ableton.com/schema/song/1.4.8/devicePreset.json",
    "kind": "instrumentRack",
    "name": "Test Preset",
    "parameters": {
        "Enabled": True,
        "Macro0": 0.0,
        "Macro1": 0.0,
        "Macro2": 0.0,
        "Macro3": 0.0
    },
    "chains": [
        {
            "name": "",
            "devices": [
                {
                    "kind": "instrumentRack",
                    "name": "Inner Rack",
                    "parameters": {
                        "Enabled": True,
                        "Macro0": {
                            "value": 127.0,
                            "customName": "Filter Cutoff"
                        },
                        "Macro1": 0.0,
                        "Macro2": 0.0,
                        "Macro3": 0.0
                    }
                }
            ]
        }
    ]
}

# Write the test preset to a file
test_preset_path = "examples/test_preset.json"
with open(test_preset_path, 'w') as f:
    json.dump(test_preset, f, indent=2)

print("Before update:")
print(f"Top-level Macro0: {test_preset['parameters']['Macro0']}")
print(f"Inner Rack Macro0: {test_preset['chains'][0]['devices'][0]['parameters']['Macro0']}")

# Update macro names
macro_updates = {0: "Test Macro 0", 1: "Test Macro 1"}
update_result = update_preset_macro_names(test_preset_path, macro_updates)
print(f"Update result: {update_result}")

# Load the updated preset
with open(test_preset_path, 'r') as f:
    updated_preset = json.load(f)

print("After update:")
print(f"Top-level Macro0: {updated_preset['parameters']['Macro0']}")
print(f"Inner Rack Macro0: {updated_preset['chains'][0]['devices'][0]['parameters']['Macro0']}")

# Clean up
os.remove(test_preset_path)
