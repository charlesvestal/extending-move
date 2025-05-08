#!/usr/bin/env python3
import os
import json
import shutil
from urllib.parse import quote
from scipy.io import wavfile
import numpy as np
import zipfile
import subprocess
from core.refresh_handler import refresh_library

def cleanup_temp_files(files_to_cleanup):
    """
    Clean up temporary files and directories.
    
    Args:
        files_to_cleanup: List of file/directory paths to remove
    
    Note:
        Handles both files and directories, logging any cleanup failures
        without raising exceptions.
    """
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
    Generates a Move Choke Kit template with 16 drum cell chains.
    
    This creates a Move preset file structure that includes:
    - An instrument rack containing a drum rack
    - 16 drum cells with MIDI notes 36-51
    - Each cell in a choke group for one-shot behavior
    - Default envelope settings for clean sample playback
    - A reverb return track
    - A saturator for additional processing
    
    Args:
        preset_name: Name to use for the preset
    
    Returns:
        dict: Complete Move preset structure following the schema:
              http://tech.ableton.com/schema/song/1.4.4/devicePreset.json
    
    Note:
        Each drum cell initially has a placeholder sampleUri that will
        be updated later with actual slice file paths.
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
                    "parameters": {"Voice_Envelope_Hold": 60.0},  # Prevents sample truncation
                    "deviceData": {
                        # Placeholder URI; will be replaced later
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
                "receivingNote": 36 + i,  # MIDI notes 36-51
                "sendingNote": 60,
                "chokeGroup": 1  # All cells in same choke group
            }
        }
        drum_cells.append(cell)
    
    # Create the full preset structure
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
    Slice a WAV file into multiple parts based on regions or equal divisions.
    
    Args:
        input_wav: Path to input WAV file
        out_dir: Base output directory (unused, kept for compatibility)
        regions: Optional list of dicts with 'start' and 'end' times in seconds
        num_slices: Number of equal slices if regions not provided (default: 16)
        target_directory: Directory to save slice files (default: ./Samples)
    
    Returns:
        list: Paths to created slice files
    
    The function can operate in two modes:
    1. Region-based slicing: Uses provided regions with start/end times
    2. Equal slicing: Divides file into num_slices equal parts
    
    Each slice is saved as a WAV file with format:
    {original_name}_slice_XX.wav where XX is the slice number (01-16)
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
        # Region-based slicing
        if not isinstance(regions, list):
            print("Error: 'regions' should be a list of dictionaries with 'start' and 'end' keys.")
            return slice_paths
        regions = sorted(regions, key=lambda r: r.get('start', 0))
        print(f"Number of regions received: {len(regions)}")
        for idx, region in enumerate(regions):
            start_time = region.get('start')
            end_time = region.get('end', start_time + 1)

            # Validate region times
            if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
                print(f"Warning: Region {idx+1} has invalid 'start' or 'end' times. Skipping.")
                continue

            if start_time >= end_time:
                print(f"Warning: Region {idx+1} start_time >= end_time. Skipping.")
                continue

            # Clamp times to file duration
            start_time = max(0, start_time)
            end_time = min(duration, end_time)
            start_sample = int(start_time * samplerate)
            end_sample = int(end_time * samplerate)

            if end_sample <= start_sample:
                print(f"Warning: Slice {idx+1} has zero length. Skipping.")
                continue

            # Extract and save slice
            slice_data = data[start_sample:end_sample]
            filename = f"{base}_slice_{idx+1:02d}.wav"
            path = os.path.join(target_directory, filename)
            unique_path = get_unique_filename(path)
            wavfile.write(unique_path, samplerate, slice_data)
            print(f"Exported slice {idx+1}: {unique_path}")
            slice_paths.append(unique_path)
    else:
        # Equal slicing
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

            # Extract and save slice
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
    Generate a unique filename by appending a number if file exists.
    
    Args:
        path: Desired file path
    
    Returns:
        str: A unique path that doesn't exist on disk
        
    Example:
        If "file.wav" exists, returns "file 2.wav"
        If that exists too, returns "file 3.wav", etc.
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

def update_drumcell_sample_uris(data, slices_info, sliced_filename, current_index=0, base_uri="Samples/", total_duration=None):
    """
    Update drum cell sample URIs and playback parameters in a Move preset.
    
    Args:
        data: Move preset data structure to update
        slices_info: List of (offset, hold) tuples for each slice
        sliced_filename: Path to the single sliced WAV file
        current_index: Current slice index (for recursive calls)
        base_uri: Base URI for sample references
    
    Returns:
        int: Updated current_index
    
    This function recursively walks the preset structure, finding drum cells
    and updating their sampleUri and playback parameters. All cells reference
    the same WAV file but with different playback start points and durations.
    """
    # Compute total_duration once
    if total_duration is None:
        try:
            samplerate, samples = wavfile.read(sliced_filename)
            total_duration = len(samples) / samplerate
        except Exception:
            total_duration = 1.0  # fallback to prevent division by zero
    from urllib.parse import quote
    if isinstance(data, dict):
        if data.get("kind") == "drumCell" and "deviceData" in data and "sampleUri" in data["deviceData"]:
            if slices_info and current_index < len(slices_info):
                filename = os.path.basename(sliced_filename)
                encoded_filename = quote(filename)
                new_uri = base_uri + encoded_filename
                data["deviceData"]["sampleUri"] = new_uri
                if "parameters" not in data:
                    data["parameters"] = {}
                offset, hold = slices_info[current_index]
                data["parameters"]["Voice_PlaybackStart"] = offset
                data["parameters"]["Voice_Envelope_Hold"] = hold
                data["parameters"]["Voice_Envelope_Decay"] = 0.0
                # Add playback length as fraction of full file
                playback_length = hold / total_duration if total_duration > 0 else 0
                data["parameters"]["Voice_PlaybackLength"] = playback_length
                print(f"Updated drumCell sampleUri to {new_uri} with Voice_PlaybackStart {offset} and Voice_Envelope_Hold {hold}")
                current_index += 1
            else:
                data["deviceData"]["sampleUri"] = None
                print("No slice info available. Set drumCell sampleUri to null.")
        for key, value in data.items():
            current_index = update_drumcell_sample_uris(value, slices_info, sliced_filename, current_index, base_uri, total_duration)
    elif isinstance(data, list):
        for item in data:
            current_index = update_drumcell_sample_uris(item, slices_info, sliced_filename, current_index, base_uri, total_duration)
    return current_index

def create_bundle(preset_filename, slice_paths, bundle_name):
    """
    Create a Move preset bundle containing preset and slice files.
    
    Args:
        preset_filename: Path to the preset JSON file
        slice_paths: List of paths to slice WAV files
        bundle_name: Name for the output bundle file
    
    Creates a ZIP file with:
    - Preset.ablpreset at the root
    - Samples/ directory containing only the slice files
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
    Process a WAV file into a Move drum kit preset.
    
    Args:
        input_wav: Path to input WAV file
        preset_name: Optional name for the preset (default: input filename)
        regions: Optional list of time regions for slicing
        num_slices: Number of equal slices if regions not provided (default: 16)
        keep_files: Whether to keep temporary files (default: False)
        mode: Either "download" or "auto_place" (default: "download")
    
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
            - bundle_path: Path to created bundle (download mode only)
    
    The function operates in two modes:
    1. Download mode:
       - Creates a downloadable .ablpresetbundle file
       - Bundle contains preset and samples
    
    2. Auto-place mode:
       - Places files directly in Move's library
       - Samples go to UserLibrary/Samples/Preset Samples
       - Preset goes to UserLibrary/Track Presets
       - Refreshes library cache automatically
    """
    temp_files = []  # Track files to clean up
    try:
        # Parse regions if provided as JSON string
        if isinstance(regions, str):
            regions = json.loads(regions)
            print(f"Parsed regions from JSON string: {regions}")
        
        # Determine preset name
        if preset_name:
            preset = preset_name
        else:
            preset = os.path.splitext(os.path.basename(input_wav))[0]
            print(f"No preset name provided; defaulting to '{preset}'.")

        # Generate the kit template
        kit_template = generate_choke_kit_template(preset)

        if mode == "download":
            # Set up paths for bundle creation
            samples_folder = "Samples"
            preset_output_file = "Preset.ablpreset"
            bundle_filename = f"{preset}.ablpresetbundle"

            # Track temporary files for cleanup
            temp_files.extend([samples_folder, preset_output_file])

            os.makedirs(samples_folder, exist_ok=True)
            
            # Copy the entire WAV file with -sliced suffix
            os.makedirs(samples_folder, exist_ok=True)
            base = os.path.splitext(os.path.basename(input_wav))[0]
            sliced_wav = os.path.join(samples_folder, base + "-sliced.wav")
            shutil.copy2(input_wav, sliced_wav)

            # Compute total duration of the WAV file
            from scipy.io import wavfile
            samplerate, data = wavfile.read(sliced_wav)
            total_duration = len(data) / samplerate

            if regions:
                slices_info = []
                for region in regions:
                    start = float(region.get("start", 0))
                    end = float(region.get("end", start))
                    hold = end - start
                    offset = start / total_duration if total_duration > 0 else 0
                    slices_info.append((offset, hold))
            else:
                num_slices = num_slices if num_slices is not None else 16
                slice_duration = total_duration / num_slices
                slices_info = []
                for i in range(num_slices):
                    offset = i / num_slices
                    hold = slice_duration
                    slices_info.append((offset, hold))

            # Update the template using the single sliced file and slices_info
            update_drumcell_sample_uris(kit_template, slices_info, sliced_wav, base_uri="Samples/")

            # Save the preset file
            try:
                with open(preset_output_file, "w") as f:
                    json.dump(kit_template, f, indent=2)
            except Exception as e:
                cleanup_temp_files(temp_files)
                return {'success': False, 'message': f"Could not write preset file: {e}"}

            # Create the bundle
            create_bundle(preset_output_file, [sliced_wav], bundle_filename)
            temp_files.append(bundle_filename)

            # Clean up temporary files except the bundle
            if not keep_files:
                cleanup_temp_files(temp_files[:-1])

            return {'success': True, 'bundle_path': bundle_filename, 'message': "Preset bundle created successfully."}

        elif mode == "auto_place":
            # Set up paths for direct placement
            samples_target_dir = "/data/UserData/UserLibrary/Samples/Preset Samples"
            presets_target_dir = "/data/UserData/UserLibrary/Track Presets"
            preset_output_file = os.path.join(presets_target_dir, f"{preset}.ablpreset")

            os.makedirs(samples_target_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(input_wav))[0]
            sliced_wav = os.path.join(samples_target_dir, base + "-sliced.wav")
            shutil.copy2(input_wav, sliced_wav)

            from scipy.io import wavfile
            samplerate, data = wavfile.read(sliced_wav)
            total_duration = len(data) / samplerate

            if regions:
                slices_info = []
                for region in regions:
                    start = float(region.get("start", 0))
                    end = float(region.get("end", start))
                    hold = end - start
                    offset = start / total_duration if total_duration > 0 else 0
                    slices_info.append((offset, hold))
            else:
                num_slices = num_slices if num_slices is not None else 16
                slice_duration = total_duration / num_slices
                slices_info = []
                for i in range(num_slices):
                    offset = i / num_slices
                    hold = slice_duration
                    slices_info.append((offset, hold))

            update_drumcell_sample_uris(kit_template, slices_info, sliced_wav, base_uri="ableton:/user-library/Samples/Preset%20Samples/")

            # Save the preset file
            try:
                with open(preset_output_file, "w") as f:
                    json.dump(kit_template, f, indent=2)
            except Exception as e:
                cleanup_temp_files([sliced_wav])  # Clean up created sample files
                return {'success': False, 'message': f"Could not write preset file: {e}"}

            # Refresh the library to show new files
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
