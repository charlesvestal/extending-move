import os
import json
from collections import deque

TRACK_PRESETS_DIR = "/data/UserData/UserLibrary/Track Presets"

def inspect_drum_racks(directory):
    """
    Inspects all JSON and .ablpreset files in the specified directory and extracts sampleUris from drumCells.
    Returns a list of dictionaries containing file paths and corresponding sampleUris.
    """
    drum_rack_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.json', '.ablpreset')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    sample_uris = extract_sample_uris(data)
                    if sample_uris:
                        drum_rack_files.append({
                            'file': os.path.relpath(filepath, directory),
                            'sample_uris': sample_uris
                        })
                except json.JSONDecodeError:
                    print(f"Invalid JSON in file: {filepath}")
                except Exception as e:
                    print(f"Error reading file {filepath}: {e}")
    return drum_rack_files

def extract_sample_uris(data):
    """
    Recursively extracts sampleUris from drumCells within the JSON data.
    """
    sample_uris = []
    queue = deque([data])
    while queue:
        current = queue.popleft()
        if isinstance(current, dict):
            if current.get('kind') == 'drumCell' and 'deviceData' in current:
                device_data = current['deviceData']
                if 'sampleUri' in device_data:
                    sample_uris.append(device_data['sampleUri'])
            else:
                for value in current.values():
                    if isinstance(value, (dict, list)):
                        queue.append(value)
        elif isinstance(current, list):
            queue.extend(current)
    return sample_uris
