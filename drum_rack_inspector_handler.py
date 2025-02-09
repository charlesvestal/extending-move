import os
import json
from collections import deque

TRACK_PRESETS_DIR = "/data/UserData/UserLibrary/Track Presets"

def inspect_drum_racks(directory):
    """
    Returns a list of relative file paths to all .ablpreset files in the specified directory.
    """
    ablpreset_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.ablpreset'):
                filepath = os.path.relpath(os.path.join(root, file), directory)
                ablpreset_files.append(filepath)
    return ablpreset_files

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
def inspect_drum_rack_file(directory, relative_file_path):
    """
    Extracts sampleUris from the specified .ablpreset file.
    """
    filepath = os.path.join(directory, relative_file_path)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        sample_uris = extract_sample_uris(data)
        return sample_uris
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {filepath}")
        return []
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return []
