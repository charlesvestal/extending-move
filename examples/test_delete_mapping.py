#!/usr/bin/env python3
import sys
import json
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the function we want to test
from core.synth_preset_inspector_handler import delete_parameter_mapping

# Create a test preset file with a parameter that has a macro mapping
test_preset = {
    "$schema": "http://tech.ableton.com/schema/song/1.4.8/devicePreset.json",
    "kind": "instrumentRack",
    "name": "Test Preset",
    "chains": [
        {
            "name": "",
            "devices": [
                {
                    "kind": "drift",
                    "name": "Test Device",
                    "parameters": {
                        "Enabled": True,
                        "Filter_Frequency": {
                            "value": 19999.99609375,
                            "macroMapping": {
                                "macroIndex": 0,
                                "rangeMin": 20.0,
                                "rangeMax": 19999.99609375
                            }
                        },
                        "Filter_Resonance": 0.20000000298023224
                    }
                }
            ]
        }
    ]
}

# Write the test preset to a file
test_preset_path = "examples/test_delete_preset.json"
with open(test_preset_path, 'w') as f:
    json.dump(test_preset, f, indent=2)

print("Before delete:")
print(f"Filter_Frequency: {test_preset['chains'][0]['devices'][0]['parameters']['Filter_Frequency']}")
print(f"Filter_Resonance: {test_preset['chains'][0]['devices'][0]['parameters']['Filter_Resonance']}")

# Delete the mapping
param_path = "chains[0].devices[0].parameters.Filter_Frequency"
delete_result = delete_parameter_mapping(test_preset_path, param_path)
print(f"Delete result: {delete_result}")

# Load the updated preset
with open(test_preset_path, 'r') as f:
    updated_preset = json.load(f)

print("After delete:")
print(f"Filter_Frequency: {updated_preset['chains'][0]['devices'][0]['parameters']['Filter_Frequency']}")
print(f"Filter_Resonance: {updated_preset['chains'][0]['devices'][0]['parameters']['Filter_Resonance']}")

# Clean up
os.remove(test_preset_path)
