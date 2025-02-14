#!/usr/bin/env python3
import os

def sample_editor():
    """
    Main function that implements your feature's logic.
    
    Parameters:
    - param1: Description of param1
    - param2: Description of param2
    
    Returns:
    A dictionary with keys:
    - 'success': bool
    - 'message': str
    - Additional keys as needed
    """
    try:
        # Your implementation here
        return {
            'success': True,
            'message': 'Operation completed successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


def get_wav_files(directory):
    """
    Retrieves a list of WAV files from the specified directory.
    """
    wav_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.wav'):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                wav_files.append(relative_path)
    ## print(f"Recursively found WAV files: {wav_files}")  # Debugging statement
    return wav_files