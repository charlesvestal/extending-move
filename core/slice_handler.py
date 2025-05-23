#!/usr/bin/env python3
import os
import json
import shutil
import zipfile
import soundfile as sf
from core.refresh_handler import refresh_library

import librosa

def detect_transients(filepath, max_slices=16, delta=0.07):
    """
    Detect transient points (onsets) in the audio file.
    Args:
        filepath: path to audio
        max_slices: maximum number of regions to return
        delta: sensitivity threshold for onset detection
    Returns: regions list [{start, end}, ...] (in seconds, up to max_slices)
    """
    y, sr = librosa.load(filepath, sr=None, mono=True)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time', delta=delta)
    if len(onsets) == 0:
        duration = librosa.get_duration(y=y, sr=sr)
        return [{"start": 0.0, "end": duration}]
    # Start slices at the first detected transient rather than the file start
    slice_points = list(onsets)
    duration = librosa.get_duration(y=y, sr=sr)
    if slice_points[-1] < duration:
        slice_points.append(duration)
    regions = []
    for i in range(len(slice_points)-1):
        start, end = slice_points[i], slice_points[i+1]
        if end - start > 0.01:
            regions.append({"start": start, "end": end})
    # Limit to first max_slices if a limit is specified
    if max_slices is not None and len(regions) > max_slices:
        return regions[:max_slices]
    else:
        return regions

# using SoundFile for robust WAV/AIFF slicing

# Remove self-import if present
# from core.slice_handler import slice_wav  # <-- REMOVE THIS LINE IF PRESENT

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

def generate_kit_template(preset_name, kit_type='choke'):
    if not isinstance(preset_name, str):
        preset_name = str(preset_name) if hasattr(preset_name, "__str__") else "Preset"
    """
    Generates a Move Kit template with 16 drum cell chains, supporting choke, gate, or drum kit types.

    Args:
        preset_name: Name to use for the preset
        kit_type: One of 'choke', 'gate', or 'drum'

    Returns:
        dict: Complete Move preset structure following the schema:
              http://tech.ableton.com/schema/song/1.4.4/devicePreset.json

    Kit behaviors:
        - "choke": Voice_Envelope_Hold=60.0, chokeGroup=1, Voice_Envelope_Mode="A-H-D"
        - "gate": Voice_Envelope_Hold=0.6, chokeGroup=None, Voice_Envelope_Mode="A-S-R"
        - "drum": Voice_Envelope_Hold=0.6, chokeGroup=None, Voice_Envelope_Mode="A-H-D"
    """
    # Set kit type parameters
    if kit_type == "choke":
        envelope_hold = 60.0
        choke_group = 1
        envelope_mode = "A-H-D"
    elif kit_type == "gate":
        envelope_hold = 0.6
        choke_group = None
        envelope_mode = "A-S-R"
    elif kit_type == "drum":
        envelope_hold = 0.6
        choke_group = None
        envelope_mode = "A-H-D"
    else:
        # fallback to choke kit if unrecognized
        envelope_hold = 60.0
        choke_group = 1
        envelope_mode = "A-S-R"

    drum_cells = []
    for i in range(16):
        drum_zone_settings = {
            "receivingNote": 36 + i,
            "sendingNote": 60,
            "chokeGroup": choke_group
        }
        cell = {
            "name": "",
            "color": 0,
            "devices": [
                {
                    "presetUri": None,
                    "kind": "drumCell",
                    "name": "",
                    "parameters": {
                        "Voice_Envelope_Hold": envelope_hold,
                        "Voice_Envelope_Mode": envelope_mode,
                    },
                    "deviceData": {
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
            "drumZoneSettings": drum_zone_settings
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

def slice_wav(input_file, regions=None, num_slices=16, target_directory="./Samples"):
    """
    Copy the original audio file (WAV or AIFF) to the target directory,
    preserving its extension. Playback regions will be handled via the preset.
    Returns:
        list of one path: the copied file.
    """
    os.makedirs(target_directory, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(input_file))
    # Copy file with suffix '-sliced' and preserve extension
    dest = os.path.join(target_directory, f"{base}-sliced{ext}")
    unique_dest = get_unique_filename(dest)
    shutil.copy2(input_file, unique_dest)
    return [unique_dest]

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

    Only updates Voice_Envelope_Hold if it is currently 60.0 (the default for choke kit),
    so user-set values from the template (e.g., 0.6 for gate/drum) are respected.
    """
    # Compute total_duration once
    if total_duration is None:
        try:
            import soundfile as sf
            samples, samplerate = sf.read(sliced_filename, dtype='int32')
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
                # Only update Voice_Envelope_Hold if it is currently 60.0
                if data["parameters"].get("Voice_Envelope_Hold", None) == 60.0:
                    data["parameters"]["Voice_Envelope_Hold"] = 60.0
                # Always update Decay and PlaybackLength as before
                data["parameters"]["Voice_Envelope_Decay"] = 0.0
                playback_length = hold / total_duration if total_duration > 0 else 0
                data["parameters"]["Voice_PlaybackLength"] = playback_length
                print(f"Updated drumCell sampleUri to {new_uri} with Voice_PlaybackStart {offset} and Voice_Envelope_Hold {data['parameters'].get('Voice_Envelope_Hold')}")
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
               mode="download", kit_type="choke", transient_detect=False):
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
    """
    See docstring above for details.
    """
    # Prevent preset_name from being a dict (or any non-str)
    if preset_name is not None and not isinstance(preset_name, str):
        preset_name = str(preset_name) if hasattr(preset_name, "__str__") else "Preset"
    temp_files = []  # Track files to clean up
    try:
        # If transient detection is requested, generate regions
        if transient_detect:
            regions = detect_transients(input_wav, max_slices=16)
            num_slices = None
        # Parse regions if provided as JSON string
        if isinstance(regions, str):
            regions = json.loads(regions)
        
        # Determine preset name
        if preset_name:
            preset = preset_name
        else:
            preset = os.path.splitext(os.path.basename(input_wav))[0]
        # Generate the kit template
        kit_template = generate_kit_template(preset, kit_type=kit_type)

        if mode == "download":
            # Set up paths for bundle creation
            samples_folder = "Samples"
            preset_output_file = "Preset.ablpreset"
            bundle_filename = f"{preset}.ablpresetbundle"

            # Track temporary files for cleanup
            temp_files.extend([samples_folder, preset_output_file])

            # Create sliced file via slice_wav (preserves extension)
            sliced_list = slice_wav(input_wav, regions=regions, num_slices=num_slices, target_directory=samples_folder)
            sliced_wav = sliced_list[0]

            # Compute total duration of the audio file using SoundFile
            data, samplerate = sf.read(sliced_wav, dtype='int32')
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

            # Create sliced file via slice_wav (preserves extension)
            sliced_list = slice_wav(input_wav, regions=regions, num_slices=num_slices, target_directory=samples_target_dir)
            sliced_wav = sliced_list[0]

            # Compute total duration of the audio file using SoundFile
            data, samplerate = sf.read(sliced_wav, dtype='int32')
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
        return {'success': False, 'message': f"Error processing kit in: {e}"}
