#!/usr/bin/env python3
import os
import json
import shutil
from urllib.parse import quote
from scipy.io import wavfile
import numpy as np
import zipfile

# ==========================
# 1. KIT TEMPLATE GENERATOR
# ==========================
def generate_choke_kit_template(preset_name):
    """
    Generates a Choke Kit template with 16 drum cell chains.
    Each cell gets a placeholder sampleUri that will be updated later.
    The top-level "name" is set to preset_name.
    Receiving notes are assigned from 36 to 51.
    
    Each drum cell's device has a parameters object that includes:
         "Voice_Envelope_Hold": 60.0
    """
    drum_cells = []
    for i in range(16):
        cell = {
            "name": "",
            "color": 0,
            "devices": [
                {
                    "presetUri": None,
                    "kind": "drumCell",
                    "name": "",
                    "parameters": {"Voice_Envelope_Hold": 60.0},
                    "deviceData": {
                        # Placeholder URI; will be replaced later.
                        "sampleUri": f"ableton:/user-library/Samples/Preset%20Samples/Placeholder_slice_{i+1:02d}.wav"
                    }
                }
            ],
            "mixer": {
                "pan": 0.0,
                "solo-cue": False,
                "speakerOn": True,
                "volume": 0.0,
                "sends": [{"isEnabled": True, "amount": -70.0}]
            },
            "drumZoneSettings": {
                "receivingNote": 36 + i,
                "sendingNote": 60,
                "chokeGroup": 1
            }
        }
        drum_cells.append(cell)
    
    template = {
        "$schema": "http://tech.ableton.com/schema/song/1.4.4/devicePreset.json",
        "kind": "instrumentRack",
        "name": preset_name,  # Use the chosen preset name.
        "lockId": 1001,
        "lockSeal": -973461132,
        "parameters": {
            "Enabled": True,
            "Macro0": 0.0,
            "Macro1": 0.0,
            "Macro2": 0.0,
            "Macro3": 0.0,
            "Macro4": 0.0,
            "Macro5": 0.0,
            "Macro6": 0.0,
            "Macro7": 0.0
        },
        "chains": [
            {
                "name": "",
                "color": 0,
                "devices": [
                    {
                        "presetUri": None,
                        "kind": "drumRack",
                        "name": "",
                        "lockId": 1001,
                        "lockSeal": 830049224,
                        "parameters": {
                            "Enabled": True,
                            "Macro0": 0.0,
                            "Macro1": 0.0,
                            "Macro2": 0.0,
                            "Macro3": 0.0,
                            "Macro4": 0.0,
                            "Macro5": 0.0,
                            "Macro6": 0.0,
                            "Macro7": 0.0
                        },
                        "chains": drum_cells,
                        "returnChains": [
                            {
                                "name": "",
                                "color": 0,
                                "devices": [
                                    {
                                        "presetUri": None,
                                        "kind": "reverb",
                                        "name": "",
                                        "parameters": {},
                                        "deviceData": {}
                                    }
                                ],
                                "mixer": {
                                    "pan": 0.0,
                                    "solo-cue": False,
                                    "speakerOn": True,
                                    "volume": 0.0,
                                    "sends": [{"isEnabled": False, "amount": -70.0}]
                                }
                            }
                        ]
                    },
                    {
                        "presetUri": None,
                        "kind": "saturator",
                        "name": "Saturator",
                        "parameters": {},
                        "deviceData": {}
                    }
                ],
                "mixer": {
                    "pan": 0.0,
                    "solo-cue": False,
                    "speakerOn": True,
                    "volume": 0.0,
                    "sends": []
                }
            }
        ]
    }
    return template

# ==========================
# 2. AUDIO SLICING
# ==========================
def slice_wav(input_wav, out_dir, num_slices=16, target_directory="./Samples"):
    """
    Reads the input WAV file, splits it into num_slices equal parts,
    and writes them to out_dir.
    If target_directory is provided, slices are saved there instead of out_dir.
    Returns a list of file paths (one per slice).
    """
    samplerate, data = wavfile.read(input_wav)
    total_samples = data.shape[0]
    slice_samples = total_samples // num_slices

    os.makedirs(target_directory, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_wav))[0]
    slice_paths = []

    for i in range(num_slices):
        start = i * slice_samples
        end = total_samples if i == num_slices - 1 else (i + 1) * slice_samples
        slice_data = data[start:end]
        filename = f"{base}_slice_{i+1:02d}.wav"
        path = os.path.join(target_directory, filename)
        
        # Ensure unique filename
        unique_path = get_unique_filename(path)
        wavfile.write(unique_path, samplerate, slice_data)
        print(f"Exported slice {i+1} to {unique_path}")
        slice_paths.append(unique_path)
    return slice_paths

def get_unique_filename(path):
    """
    If the file at 'path' exists, append a number to make it unique.
    """
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 2
    while True:
        new_path = f"{base} {counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1

# ==========================
# 3. UPDATE DRUM CELL SAMPLE URIs
# ==========================
def update_drumcell_sample_uris(data, slice_paths, current_index=0, base_uri="Samples/"):
    """
    Recursively walks the JSON data. When a dictionary with "kind" == "drumCell" is found
    and it has a key "deviceData" containing "sampleUri", replace that value with:
       base_uri + URI-encoded(basename of next slice file)
    The slices are used in document order.
    Returns the updated current_index.
    
    If there are not enough slice files, the remaining drum cells are left with sampleUri as null.
    """
    if isinstance(data, dict):
        if data.get("kind") == "drumCell" and "deviceData" in data and "sampleUri" in data["deviceData"]:
            if current_index < len(slice_paths):
                filename = os.path.basename(slice_paths[current_index])
                encoded_filename = quote(filename)
                new_uri = base_uri + encoded_filename
                data["deviceData"]["sampleUri"] = new_uri
                print(f"Updated drumCell sampleUri to {new_uri}")
                current_index += 1
            else:
                data["deviceData"]["sampleUri"] = None
                print("No slice available. Set drumCell sampleUri to null.")
        for key, value in data.items():
            current_index = update_drumcell_sample_uris(value, slice_paths, current_index, base_uri)
    elif isinstance(data, list):
        for item in data:
            current_index = update_drumcell_sample_uris(item, slice_paths, current_index, base_uri)
    return current_index

# ==========================
# 4. BUNDLE CREATION
# ==========================
def create_bundle(preset_filename, samples_folder, bundle_name):
    """
    Creates a ZIP file (bundle) named bundle_name (with extension .ablpresetbundle)
    that contains the preset file and the samples folder (with its directory structure).
    """
    with zipfile.ZipFile(bundle_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add the preset file at the root of the zip.
        zf.write(preset_filename, arcname=os.path.basename(preset_filename))
        print(f"Added {preset_filename} as {os.path.basename(preset_filename)}")
        # Walk through the samples folder and add its files.
        for root, dirs, files in os.walk(samples_folder):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, os.path.dirname(samples_folder))
                zf.write(fullpath, arcname=arcname)
                print(f"Added {fullpath} as {arcname}")

# ==========================
# 5. PROCESS KIT GENERATION
# ==========================
def process_kit(input_wav, preset_name=None, num_slices=16, keep_files=False, 
               mode="download"):
    """
    Processes the kit generation by slicing the WAV file, updating the kit template,
    and creating a preset bundle or placing it automatically.
    
    Parameters:
    - input_wav: Path to the input WAV file.
    - preset_name: Name of the preset.
    - num_slices: Number of slices to generate.
    - keep_files: Whether to keep intermediate files.
    - mode: "download" or "auto_place".
    """
    # If preset_name is provided, use it; otherwise, default to the input WAV file's base name.
    if preset_name:
        preset = preset_name
    else:
        preset = os.path.splitext(os.path.basename(input_wav))[0]
        print(f"No preset name provided; defaulting to '{preset}'.")

    # Check if Samples folder or Preset.ablpreset file exist.
    existing_outputs = []
    if mode == "download":
        if os.path.exists("Samples"):
            existing_outputs.append("Samples")
        if os.path.exists("Preset.ablpreset"):
            existing_outputs.append("Preset.ablpreset")
    elif mode == "auto_place":
        samples_target_dir = "/data/UserData/UserLibrary/Samples/Preset Samples"
        presets_target_dir = "/data/UserData/UserLibrary/Track Presets"
        preset_output_file = os.path.join(presets_target_dir, f"{preset}.ablpreset")
        if os.path.exists(samples_target_dir):
            pass  # We'll handle individual files
        if os.path.exists(preset_output_file):
            existing_outputs.append(preset_output_file)
    
    if existing_outputs:
        print(f"The following files/folders already exist: {', '.join(existing_outputs)}. Deleting them.")
        for item in existing_outputs:
            if os.path.isdir(item):
                shutil.rmtree(item)
                print(f"Deleted existing folder: {item}")
            else:
                os.remove(item)
                print(f"Deleted existing file: {item}")

    # Currently only "Choke Kit" is supported.
    kit_type = "Choke Kit"
    kit_template = generate_choke_kit_template(preset)

    if mode == "download":
        samples_folder = "Samples"         # Slices will be exported here.
        preset_output_file = "Preset.ablpreset"  # Updated preset JSON file.
        bundle_filename = f"{preset}.ablpresetbundle"  # Final bundle ZIP filename.

        # Slice the input WAV file.
        slice_paths = slice_wav(input_wav, samples_folder, num_slices=num_slices, target_directory=samples_folder)

        # Update the kit template: Replace each drum cell's sampleUri with "Samples/<URI-encoded-slice-filename>" or leave null.
        update_drumcell_sample_uris(kit_template, slice_paths, base_uri="Samples/")

        # Write the updated preset JSON to Preset.ablpreset.
        with open(preset_output_file, "w") as f:
            json.dump(kit_template, f, indent=2)
        print(f"Updated preset written to {preset_output_file}")

        # Create a bundle (ZIP) that contains Preset.ablpreset and the Samples folder.
        create_bundle(preset_output_file, samples_folder, bundle_filename)
        print(f"Created bundle: {bundle_filename}")

        # Optionally clean up intermediate files.
        if not keep_files:
            if os.path.exists("Samples"):
                shutil.rmtree("Samples")
                print("Deleted Samples folder.")
            if os.path.exists(preset_output_file):
                os.remove(preset_output_file)
                print("Deleted Preset.ablpreset file.")

    elif mode == "auto_place":
        samples_target_dir = "/data/UserData/UserLibrary/Samples/Preset Samples"
        presets_target_dir = "/data/UserData/UserLibrary/Track Presets"
        preset_output_file = os.path.join(presets_target_dir, f"{preset}.ablpreset")

        # Slice the input WAV file.
        slice_paths = slice_wav(input_wav, "/data/UserData/UserLibrary/Samples/Preset Samples", num_slices=num_slices)

        # Update the kit template: Replace each drum cell's sampleUri with "ableton:/user-library/Samples/Preset%20Samples/<URI-encoded-slice-filename>" or leave null.
        update_drumcell_sample_uris(kit_template, slice_paths, base_uri="ableton:/user-library/Samples/Preset%20Samples/")

        # Write the updated preset JSON to the target preset path.
        with open(preset_output_file, "w") as f:
            json.dump(kit_template, f, indent=2)
        print(f"Updated preset written to {preset_output_file}")

        # Optionally clean up intermediate files.
        if not keep_files:
            for path in slice_paths:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted slice file: {path}")

    else:
        raise ValueError("Invalid mode. Must be 'download' or 'auto_place'.")
