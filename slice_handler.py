#!/usr/bin/env python3
import os
import json
import shutil
from urllib.parse import quote
from scipy.io import wavfile
import numpy as np
import zipfile
import subprocess
from refresh_handler import refresh_library

def cleanup_temp_files(files_to_cleanup):
    """Clean up temporary files and directories."""
    for path in files_to_cleanup:
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        except Exception as e:
            print(f"Warning: Failed to clean up {path}: {e}")

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
        "name": preset_name,
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

def slice_wav(input_wav, out_dir, regions=None, num_slices=16, target_directory="./Samples"):
    """
    Reads the input WAV file, splits it into parts based on the provided regions or number of slices,
    and writes them to target_directory.
    Returns a list of file paths (one per slice).
    """
    samplerate, data = wavfile.read(input_wav)
    total_samples = data.shape[0]
    duration = total_samples / samplerate
    print(f"Sampling rate: {samplerate} Hz")
    print(f"Total samples: {total_samples}")
    print(f"Duration: {duration} seconds")
    
    os.makedirs(target_directory, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_wav))[0]
    slice_paths = []

    if regions is not None:
        if not isinstance(regions, list):
            print("Error: 'regions' should be a list of dictionaries with 'start' and 'end' keys.")
            return slice_paths
        regions = sorted(regions, key=lambda r: r.get('start', 0))
        print(f"Number of regions received: {len(regions)}")
        for idx, region in enumerate(regions):
            start_time = region.get('start')
            end_time = region.get('end', start_time + 1)

            if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
                print(f"Warning: Region {idx+1} has invalid 'start' or 'end' times. Skipping.")
                continue

            if start_time >= end_time:
                print(f"Warning: Region {idx+1} start_time >= end_time. Skipping.")
                continue

            start_time = max(0, start_time)
            end_time = min(duration, end_time)
            start_sample = int(start_time * samplerate)
            end_sample = int(end_time * samplerate)

            if end_sample <= start_sample:
                print(f"Warning: Slice {idx+1} has zero length. Skipping.")
                continue

            slice_data = data[start_sample:end_sample]
            filename = f"{base}_slice_{idx+1:02d}.wav"
            path = os.path.join(target_directory, filename)
            unique_path = get_unique_filename(path)
            wavfile.write(unique_path, samplerate, slice_data)
            print(f"Exported slice {idx+1}: {unique_path}")
            slice_paths.append(unique_path)
    else:
        print("No regions provided. Falling back to equal slicing.")
        slice_duration = duration / num_slices
        for i in range(num_slices):
            start_time = i * slice_duration
            end_time = (i + 1) * slice_duration
            start_sample = int(start_time * samplerate)
            end_sample = int(end_time * samplerate)

            start_time = max(0, start_time)
            end_time = min(duration, end_time)

            if end_sample <= start_sample:
                print(f"Warning: Slice {i+1} has zero length. Skipping.")
                continue

            slice_data = data[start_sample:end_sample]
            filename = f"{base}_slice_{i+1:02d}.wav"
            path = os.path.join(target_directory, filename)
            unique_path = get_unique_filename(path)
            wavfile.write(unique_path, samplerate, slice_data)
            print(f"Exported slice {i+1}: {unique_path}")
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

def update_drumcell_sample_uris(data, slice_paths, current_index=0, base_uri="Samples/"):
    """
    Recursively walks the JSON data. When a dictionary with "kind" == "drumCell" is found
    and it has a key "deviceData" containing "sampleUri", replace that value with:
       base_uri + URI-encoded(basename of next slice file)
    The slices are used in document order.
    Returns the updated current_index.
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

def create_bundle(preset_filename, slice_paths, bundle_name):
    """
    Creates a ZIP file that contains the preset file and only the specified slice files.
    """
    with zipfile.ZipFile(bundle_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add the preset file at the root
        zf.write(preset_filename, arcname=os.path.basename(preset_filename))
        print(f"Added {preset_filename}")
        
        # Add only the specified slice files
        for slice_path in slice_paths:
            arcname = os.path.join("Samples", os.path.basename(slice_path))
            zf.write(slice_path, arcname=arcname)
            print(f"Added {slice_path} as {arcname}")

def process_kit(input_wav, preset_name=None, regions=None, num_slices=None, keep_files=False, 
               mode="download"):
    """
    Processes the kit generation by slicing the WAV file, updating the kit template,
    and creating a preset bundle or placing it automatically.
    """
    temp_files = []  # Track files to clean up
    try:
        if isinstance(regions, str):
            regions = json.loads(regions)
            print(f"Parsed regions from JSON string: {regions}")
        
        if preset_name:
            preset = preset_name
        else:
            preset = os.path.splitext(os.path.basename(input_wav))[0]
            print(f"No preset name provided; defaulting to '{preset}'.")

        kit_template = generate_choke_kit_template(preset)

        if mode == "download":
            samples_folder = "Samples"
            preset_output_file = "Preset.ablpreset"
            bundle_filename = f"{preset}.ablpresetbundle"

            # Track temporary files
            temp_files.extend([samples_folder, preset_output_file])

            os.makedirs(samples_folder, exist_ok=True)
            
            if regions and isinstance(regions, list) and len(regions) > 0:
                slice_paths = slice_wav(input_wav, samples_folder, regions=regions, target_directory=samples_folder)
            else:
                if num_slices is None:
                    num_slices = 16
                slice_paths = slice_wav(input_wav, samples_folder, num_slices=num_slices, target_directory=samples_folder)

            update_drumcell_sample_uris(kit_template, slice_paths, base_uri="Samples/")

            try:
                with open(preset_output_file, "w") as f:
                    json.dump(kit_template, f, indent=2)
            except Exception as e:
                cleanup_temp_files(temp_files)
                return {'success': False, 'message': f"Could not write preset file: {e}"}

            create_bundle(preset_output_file, slice_paths, bundle_filename)
            temp_files.append(bundle_filename)

            if not keep_files:
                cleanup_temp_files(temp_files[:-1])  # Keep bundle file for download

            return {'success': True, 'bundle_path': bundle_filename, 'message': "Preset bundle created successfully."}

        elif mode == "auto_place":
            samples_target_dir = "/data/UserData/UserLibrary/Samples/Preset Samples"
            presets_target_dir = "/data/UserData/UserLibrary/Track Presets"
            preset_output_file = os.path.join(presets_target_dir, f"{preset}.ablpreset")

            if regions and isinstance(regions, list) and len(regions) > 0:
                slice_paths = slice_wav(input_wav, samples_target_dir, regions=regions, target_directory=samples_target_dir)
            else:
                if num_slices is None:
                    num_slices = 16
                slice_paths = slice_wav(input_wav, samples_target_dir, num_slices=num_slices, target_directory=samples_target_dir)

            update_drumcell_sample_uris(kit_template, slice_paths, base_uri="ableton:/user-library/Samples/Preset%20Samples/")

            try:
                with open(preset_output_file, "w") as f:
                    json.dump(kit_template, f, indent=2)
            except Exception as e:
                cleanup_temp_files(slice_paths)  # Clean up created sample files
                return {'success': False, 'message': f"Could not write preset file: {e}"}

            refresh_success, refresh_message = refresh_library()
            if refresh_success:
                return {'success': True, 'message': f"Preset {preset} automatically placed successfully. {refresh_message}"}
            else:
                return {'success': True, 'message': f"Preset {preset} placed, but library refresh failed: {refresh_message}"}

        else:
            return {'success': False, 'message': "Invalid mode. Must be 'download' or 'auto_place'."}

    except Exception as e:
        cleanup_temp_files(temp_files)
        return {'success': False, 'message': f"Error processing kit: {e}"}
