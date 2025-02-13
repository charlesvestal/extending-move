#!/usr/bin/env python3
import os
import json
import urllib.parse

def update_drum_cell_sample(preset_path, pad_number, new_sample_path):
    """
    Update the sample URI for a specific drum cell in a preset.
    
    Args:
        preset_path: Path to the .ablpreset file
        pad_number: The pad number to update
        new_sample_path: The new sample path to set
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
            
        current_pad = [1]  # Use list to allow modification in nested function
        found = [False]  # Track if we found and updated the correct pad
        
        def update_drum_cells(data):
            if isinstance(data, dict):
                if data.get('kind') == 'drumCell':
                    if current_pad[0] == int(pad_number):
                        # Convert system path to Ableton URI format
                        # Encode the new sample path
                        encoded_path = urllib.parse.quote(new_sample_path)
                        
                        if encoded_path.startswith('/data/UserData/UserLibrary/Samples/'):
                            uri = encoded_path.replace('/data/UserData/UserLibrary/Samples/', 'ableton:/user-library/Samples/')
                        else:
                            uri = 'file://' + encoded_path
                            
                        # Update the sample URI
                        if 'deviceData' not in data:
                            data['deviceData'] = {}
                        data['deviceData']['sampleUri'] = uri
                        found[0] = True
                    current_pad[0] += 1
                    
                for value in data.values():
                    if not found[0]:  # Only continue searching if we haven't found it yet
                        update_drum_cells(value)
            elif isinstance(data, list):
                for item in data:
                    if not found[0]:  # Only continue searching if we haven't found it yet
                        update_drum_cells(item)
                        
        update_drum_cells(preset_data)
        
        if not found[0]:
            return False, f"Could not find pad {pad_number} in preset"
            
        # Save the modified preset
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
            
        return True, f"Updated sample URI for pad {pad_number}"
        
    except Exception as e:
        return False, f"Error updating drum cell sample: {e}"

def get_drum_cell_samples(preset_path):
    """
    Extract sample information from a preset's drum cells.
    
    Args:
        preset_path: Path to the .ablpreset file
    
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
            - samples: List of dicts with sample info (pad number and sample name)
    """
    try:
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)

        samples = []
        
        pad_counter = [1]  # Use list to allow modification in nested function
        
        def process_drum_cells(data):
            if isinstance(data, dict):
                if data.get('kind') == 'drumCell':
                    # Extract sample URI
                    sample_uri = data.get('deviceData', {}).get('sampleUri', '')
                    print(f"\nProcessing drum cell:")  # Debug log
                    print(f"Sample URI: {sample_uri}")  # Debug log
                    if sample_uri:
                        # Handle Ableton URI format
                        if sample_uri.startswith('ableton:/user-library/Samples/'):
                            # Convert ableton:/user-library/Samples/ to /data/UserData/UserLibrary/Samples/
                            sample_path = sample_uri.replace('ableton:/user-library/Samples/', '/data/UserData/UserLibrary/Samples/')
                        else:
                            # Fallback to original file:// handling
                            sample_path = sample_uri.split('file://')[-1]
                        
                        print(f"After path translation - Path: {sample_path}")  # Debug log
                        sample_name = os.path.basename(sample_path)
                        # URL decode both
                        sample_path = urllib.parse.unquote(sample_path)
                        sample_name = urllib.parse.unquote(sample_name)
                        print(f"Final decoded path: {sample_path}")  # Debug log
                        print(f"Final decoded name: {sample_name}")  # Debug log
                    else:
                        sample_path = ""
                        sample_name = "No sample loaded"
                    
                    # Simply use incrementing counter for pad numbers
                    samples.append({
                        'pad': pad_counter[0],
                        'sample': sample_name,
                        'path': sample_path
                    })
                    pad_counter[0] += 1
                    
                for value in data.values():
                    process_drum_cells(value)
            elif isinstance(data, list):
                for item in data:
                    process_drum_cells(item)

        process_drum_cells(preset_data)
        
        # Sort samples by pad number
        samples.sort(key=lambda x: x['pad'])
        
        return {
            'success': True,
            'message': f"Found {len(samples)} drum cell samples",
            'samples': samples
        }

    except Exception as e:
        return {
            'success': False,
            'message': f"Error getting drum cell samples: {e}",
            'samples': []
        }

def scan_for_drum_rack_presets():
    """
    Scan the Move Track Presets directory for .ablpreset files containing drumRack devices.
    
    Returns:
        dict: Result with keys:
            - success: bool indicating success/failure
            - message: Status or error message
            - presets: List of dicts with preset info (name and path)
    """
    try:
        presets_dir = "/data/UserData/UserLibrary/Track Presets"
        drum_rack_presets = []

        # Check if directory exists
        if not os.path.exists(presets_dir):
            return {
                'success': False,
                'message': f"Track Presets directory not found: {presets_dir}",
                'presets': []
            }

        # Scan all .ablpreset files
        for filename in os.listdir(presets_dir):
            if filename.endswith('.ablpreset'):
                filepath = os.path.join(presets_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        preset_data = json.load(f)
                        
                    # Function to recursively search for drumRack devices
                    def has_drum_rack(data):
                        if isinstance(data, dict):
                            if data.get('kind') == 'drumRack':
                                return True
                            return any(has_drum_rack(v) for v in data.values())
                        elif isinstance(data, list):
                            return any(has_drum_rack(item) for item in data)
                        return False

                    # If preset contains a drumRack, add it to our list
                    if has_drum_rack(preset_data):
                        preset_name = os.path.splitext(filename)[0]
                        drum_rack_presets.append({
                            'name': preset_name,
                            'path': filepath
                        })

                except Exception as e:
                    print(f"Warning: Could not parse preset {filename}: {e}")
                    continue

        return {
            'success': True,
            'message': f"Found {len(drum_rack_presets)} drum rack presets",
            'presets': drum_rack_presets
        }

    except Exception as e:
        return {
            'success': False,
            'message': f"Error scanning presets: {e}",
            'presets': []
        }
