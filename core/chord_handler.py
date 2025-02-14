#!/usr/bin/env python3
import os
import json
import shutil
import zipfile
from urllib.parse import quote
from scipy.io import wavfile
import numpy as np
from core.refresh_handler import refresh_library

# Define common chords and their semitone intervals from root
CHORDS = {
    'C': [0, 4, 7],        # C E G
    'F': [5, 9, 0],        # F A C
    'G': [7, 11, 2],       # G B D
    'Am': [9, 0, 4],       # A C E
    'Dm': [2, 5, 9],       # D F A
    'Em': [4, 7, 11],      # E G B
    'C7': [0, 4, 7, 10],   # C E G Bb
    'F7': [5, 9, 0, 3],    # F A C Eb
    'G7': [7, 11, 2, 5],   # G B D F
    'Am7': [9, 0, 4, 7],   # A C E G
    'Dm7': [2, 5, 9, 0],   # D F A C
    'Em7': [4, 7, 11, 2],  # E G B D
    'Bdim': [11, 2, 5],    # B D F
    'Caug': [0, 4, 8],     # C E G#
    'Csus4': [0, 5, 7],    # C F G
    'Cadd9': [0, 4, 7, 2]  # C E G D
}

def pitch_wav(data, sample_rate, semitones):
    """
    Pitch shift a WAV file by a number of semitones using resampling.
    
    Args:
        data: WAV data as numpy array
        sample_rate: Original sample rate
        semitones: Number of semitones to shift (positive = up, negative = down)
    
    Returns:
        tuple: (pitched_data, new_sample_rate)
    """
    # Calculate pitch shift factor (2^(1/12) for each semitone)
    factor = 2 ** (semitones / 12.0)
    
    # Calculate new length after pitch shift
    new_length = int(len(data) / factor)
    
    # Use scipy's resample to change the length while preserving sample rate
    pitched_data = np.interp(
        np.linspace(0, len(data), new_length),
        np.arange(len(data)),
        data
    ).astype(data.dtype)
    
    return pitched_data, sample_rate

def normalize_audio(data):
    """
    Normalize audio data to prevent clipping.
    
    Args:
        data: Audio data as numpy array
    
    Returns:
        numpy.ndarray: Normalized audio data
    """
    max_val = np.iinfo(data.dtype).max
    scale = max_val / np.max(np.abs(data))
    return (data * scale).astype(data.dtype)

def generate_chord_samples(input_wav, target_directory):
    """
    Generate chord variations from an input WAV file.
    
    Args:
        input_wav: Path to input WAV file
        target_directory: Directory to save generated chord files
    
    Returns:
        list: Paths to created chord files
    """
    # Create output directory
    os.makedirs(target_directory, exist_ok=True)
    
    # Read input WAV
    sample_rate, data = wavfile.read(input_wav)
    
    # Convert stereo to mono if needed
    if len(data.shape) > 1:
        data = np.mean(data, axis=1).astype(data.dtype)
    
    base = os.path.splitext(os.path.basename(input_wav))[0]
    chord_paths = []
    
    # Generate each chord
    for chord_name, intervals in CHORDS.items():
        # Create pitched versions for each note in the chord
        chord_notes = []
        for interval in intervals:
            pitched_data, _ = pitch_wav(data, sample_rate, interval)
            chord_notes.append(pitched_data)
        
        # Pad shorter arrays to match the longest
        max_length = max(len(note) for note in chord_notes)
        padded_notes = [
            np.pad(note, (0, max_length - len(note)))
            for note in chord_notes
        ]
        
        # Mix the notes together
        chord_data = sum(padded_notes)
        
        # Normalize to prevent clipping
        chord_data = normalize_audio(chord_data)
        
        # Save the chord
        filename = f"{base}_chord_{chord_name}.wav"
        filepath = os.path.join(target_directory, filename)
        wavfile.write(filepath, sample_rate, chord_data)
        chord_paths.append(filepath)
        print(f"Generated {chord_name} chord: {filepath}")
    
    return chord_paths

def generate_choke_kit_template(preset_name):
    """
    Generate a Move preset template for the chord kit.
    Similar to slice_handler's version but adapted for chords.
    """
    drum_cells = []
    for i, chord_name in enumerate(CHORDS.keys()):
        cell = {
            "name": chord_name,  # Use chord name instead of empty string
            "color": 0,
            "devices": [
                {
                    "presetUri": None,
                    "kind": "drumCell",
                    "name": chord_name,  # Use chord name here too
                    "parameters": {"Voice_Envelope_Hold": 60.0},
                    "deviceData": {
                        "sampleUri": f"ableton:/user-library/Samples/Preset%20Samples/Placeholder_chord_{i+1:02d}.wav"
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

def update_drumcell_sample_uris(data, chord_paths, current_index=0, base_uri="Samples/"):
    """
    Update drum cell sample URIs in the preset with chord file paths.
    Similar to slice_handler's version but for chord samples.
    """
    if isinstance(data, dict):
        if data.get("kind") == "drumCell" and "deviceData" in data and "sampleUri" in data["deviceData"]:
            if current_index < len(chord_paths):
                filename = os.path.basename(chord_paths[current_index])
                encoded_filename = quote(filename)
                new_uri = base_uri + encoded_filename
                data["deviceData"]["sampleUri"] = new_uri
                print(f"Updated drumCell sampleUri to {new_uri}")
                current_index += 1
            else:
                data["deviceData"]["sampleUri"] = None
                print("No chord sample available. Set drumCell sampleUri to null.")
        for key, value in data.items():
            current_index = update_drumcell_sample_uris(value, chord_paths, current_index, base_uri)
    elif isinstance(data, list):
        for item in data:
            current_index = update_drumcell_sample_uris(item, chord_paths, current_index, base_uri)
    return current_index

def create_bundle(preset_filename, chord_paths, bundle_name):
    """
    Create a Move preset bundle containing preset and chord files.
    Similar to slice_handler's version but for chord samples.
    """
    with zipfile.ZipFile(bundle_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add the preset file at the root
        zf.write(preset_filename, arcname=os.path.basename(preset_filename))
        print(f"Added {preset_filename}")
        
        # Add the chord files
        for chord_path in chord_paths:
            arcname = os.path.join("Samples", os.path.basename(chord_path))
            zf.write(chord_path, arcname=arcname)
            print(f"Added {chord_path} as {arcname}")

def process_kit(input_wav, preset_name=None, mode="download"):
    """
    Process a WAV file into a chord kit preset.
    Similar to slice_handler's version but generates chord variations.
    """
    temp_files = []
    try:
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
            
            # Generate chord samples
            chord_paths = generate_chord_samples(input_wav, samples_folder)

            # Update the template with chord paths
            update_drumcell_sample_uris(kit_template, chord_paths, base_uri="Samples/")

            # Save the preset file
            try:
                with open(preset_output_file, "w") as f:
                    json.dump(kit_template, f, indent=2)
            except Exception as e:
                cleanup_temp_files(temp_files)
                return {'success': False, 'message': f"Could not write preset file: {e}"}

            # Create the bundle
            create_bundle(preset_output_file, chord_paths, bundle_filename)
            temp_files.append(bundle_filename)

            # Clean up temporary files except the bundle
            cleanup_temp_files(temp_files[:-1])

            return {'success': True, 'bundle_path': bundle_filename, 'message': "Chord kit bundle created successfully."}

        elif mode == "auto_place":
            # Set up paths for direct placement
            samples_target_dir = "/data/UserData/UserLibrary/Samples/Preset Samples"
            presets_target_dir = "/data/UserData/UserLibrary/Track Presets"
            preset_output_file = os.path.join(presets_target_dir, f"{preset}.ablpreset")

            # Generate chord samples directly to target directory
            chord_paths = generate_chord_samples(input_wav, samples_target_dir)

            # Update the template with Move library paths
            update_drumcell_sample_uris(kit_template, chord_paths, base_uri="ableton:/user-library/Samples/Preset%20Samples/")

            # Save the preset file
            try:
                with open(preset_output_file, "w") as f:
                    json.dump(kit_template, f, indent=2)
            except Exception as e:
                cleanup_temp_files(chord_paths)
                return {'success': False, 'message': f"Could not write preset file: {e}"}

            # Refresh the library to show new files
            refresh_success, refresh_message = refresh_library()
            if refresh_success:
                return {'success': True, 'message': f"Chord kit {preset} automatically placed successfully. {refresh_message}"}
            else:
                return {'success': True, 'message': f"Chord kit {preset} placed, but library refresh failed: {refresh_message}"}

        else:
            return {'success': False, 'message': "Invalid mode. Must be 'download' or 'auto_place'."}

    except Exception as e:
        cleanup_temp_files(temp_files)
        return {'success': False, 'message': f"Error processing chord kit: {e}"}

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
