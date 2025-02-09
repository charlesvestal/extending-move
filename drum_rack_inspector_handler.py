import os
import json
import urllib.parse
from collections import deque
from reverse_handler import reverse_wav_file
from refresh_handler import refresh_library

TRACK_PRESETS_DIR = "/data/UserData/UserLibrary/Track Presets"

def inspect_drum_racks(directory):
    """
    Returns a list of relative file paths to all .ablpreset files containing a drumRack in the specified directory.
    """
    ablpreset_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.ablpreset'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if contains_drum_rack(data):
                        relative_path = os.path.relpath(filepath, directory)
                        ablpreset_files.append(relative_path)
                except json.JSONDecodeError:
                    print(f"Invalid JSON in file: {filepath}")
                except Exception as e:
                    print(f"Error reading file {filepath}: {e}")
    return ablpreset_files

def contains_drum_rack(data):
    """
    Checks if the JSON data contains a drumRack.
    """
    if isinstance(data, dict):
        if data.get('kind') == 'drumRack':
            return True
        for value in data.values():
            if isinstance(value, (dict, list)) and contains_drum_rack(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if contains_drum_rack(item):
                return True
    return False

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
                if isinstance(device_data, dict) and 'sampleUri' in device_data:
                    sample_uris.append(device_data['sampleUri'])
            else:
                for value in current.values():
                    if isinstance(value, (dict, list)):
                        queue.append(value)
        elif isinstance(current, list):
            queue.extend(current)
        # Skip other data types to prevent errors
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
def reverse_sample_and_update_preset(directory, preset_relative_path, sample_uri):
    """
    Reverses the sample file specified by sample_uri,
    updates the preset file to point to the reversed sample,
    and refreshes the library.
    Returns (success: bool, message: str)
    """
    import urllib.parse  # Ensure this is added at the top of the file

    # Handle different sample URI prefixes
    if sample_uri.startswith("UserLibrary:"):
        sample_file_relative = sample_uri.replace("UserLibrary:", "").lstrip("/")
        sample_directory = "/data/UserData/UserLibrary/Samples"
    elif sample_uri.startswith("ableton:/user-library/"):
        sample_file_relative = sample_uri.replace("ableton:/user-library/", "").lstrip("/")
        sample_directory = "/data/UserData/UserLibrary"
    else:
        # If the sample URI is in an unexpected format, return an error
        return False, f"Unsupported sample URI format: {sample_uri}"

    # URL-decode the sample file relative path
    sample_file_relative = urllib.parse.unquote(sample_file_relative)
    preset_filepath = os.path.join(directory, preset_relative_path)


    # Reverse the sample
    success, message = reverse_wav_file(sample_file_relative, sample_directory)
    if not success:
        return False, message

    # Create the new sample URI for the reversed file
    base, ext = os.path.splitext(sample_file_relative)
    reversed_sample_relative = f"{base}_reverse{ext}"
    # URL-encode the reversed sample relative path for the URI
    reversed_sample_relative_encoded = urllib.parse.quote(reversed_sample_relative)

    # Construct the new sample URI using the same prefix as the original
    if sample_uri.startswith("UserLibrary:"):
        new_sample_uri = "UserLibrary:" + reversed_sample_relative_encoded
    elif sample_uri.startswith("ableton:/user-library/"):
        new_sample_uri = "ableton:/user-library/" + reversed_sample_relative_encoded
    else:
        # Should not reach here, but include for completeness
        return False, f"Unsupported sample URI format: {sample_uri}"

    # Update the preset file to point to the reversed sample
    try:
        with open(preset_filepath, 'r') as f:
            data = json.load(f)

        updated = update_sample_uri_in_preset(data, sample_uri, new_sample_uri)
        if not updated:
            return False, "Sample URI not found in preset."

        # Write the updated preset data back to the file
        with open(preset_filepath, 'w') as f:
            json.dump(data, f)

        # Refresh the library
        refresh_success, refresh_message = refresh_library()
        if refresh_success:
            return True, "Sample reversed and preset updated successfully. Library refreshed."
        else:
            return False, f"Sample reversed and preset updated. Library refresh failed: {refresh_message}"
    except Exception as e:
        print(f"Error updating preset {preset_filepath}: {e}")
        return False, f"Error updating preset: {e}"

def update_sample_uri_in_preset(data, old_uri, new_uri):
    """
    Recursively updates the sampleUri in the preset data from old_uri to new_uri.
    Returns True if updated, False otherwise.
    """
    if isinstance(data, dict):
        if 'sampleUri' in data and data['sampleUri'] == old_uri:
            data['sampleUri'] = new_uri
            return True
        for value in data.values():
            if isinstance(value, (dict, list)):
                updated = update_sample_uri_in_preset(value, old_uri, new_uri)
                if updated:
                    return True
    elif isinstance(data, list):
        for item in data:
            updated = update_sample_uri_in_preset(item, old_uri, new_uri)
            if updated:
                return True
    return False
