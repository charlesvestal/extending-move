#!/usr/bin/env python3
import os
import json

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
