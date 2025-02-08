import os
import wave
import numpy as np
from refresh_handler import refresh_library

def get_wav_files(directory="/data/UserData/UserLibrary/Samples"):
    """
    Retrieves a list of WAV files from the specified directory.
    """
    if not os.path.isdir(directory):
        print(f"Directory does not exist: {directory}")
        return []
    
    wav_files = [f for f in os.listdir(directory) if f.lower().endswith('.wav') and os.path.isfile(os.path.join(directory, f))]
    print(f"WAV files found in {directory}: {wav_files}")  # Debugging statement
    return wav_files

def reverse_wav_file(filename, directory="/data/UserData/UserLibrary/Samples"):
    """
    Reverses the WAV file specified by filename in the given directory.
    Creates a new file with the suffix '_reverse.wav'.
    Returns a tuple (success: bool, message: str).
    """
    filepath = os.path.join(directory, filename)
    
    if not os.path.isfile(filepath):
        return False, f"File does not exist: {filepath}"
    
    try:
        # Determine new filename
        base, ext = os.path.splitext(filename)
        new_filename = f"{base}_reverse{ext}"
        new_filepath = os.path.join(directory, new_filename)
        
        # Check if the new file already exists to prevent overwriting
        if os.path.exists(new_filepath):
            return False, f"Reversed file already exists: {new_filename}"
        
        with wave.open(filepath, 'rb') as wf:
            params = wf.getparams()
            n_channels, sampwidth, framerate, n_frames, comptype, compname = params
            frames = wf.readframes(n_frames)
        
        # Determine numpy dtype based on sampwidth
        dtype_map = {
            1: np.int8,
            2: np.int16,
            3: None,   # 24-bit not directly supported
            4: np.int32
        }
        dtype = dtype_map.get(sampwidth)
        if dtype is None:
            return False, f"Unsupported sample width: {sampwidth} bytes. 24-bit WAV files are not supported."
        
        # Convert frames to numpy array
        audio_data = np.frombuffer(frames, dtype=dtype)
        
        # Reshape for multi-channel if necessary
        if n_channels > 1:
            audio_data = audio_data.reshape(-1, n_channels)
        
        # Reverse the audio data along the time axis
        reversed_data = audio_data[::-1]
        
        # Flatten back if multi-channel
        if n_channels > 1:
            reversed_data = reversed_data.reshape(-1)
        
        # Convert reversed data back to bytes
        reversed_frames = reversed_data.tobytes()
        
        # Write the reversed frames to the new WAV file
        with wave.open(new_filepath, 'wb') as wf:
            wf.setparams(params)
            wf.writeframes(reversed_frames)
        
        print(f"Successfully reversed the file: {new_filepath}")
        
        # Refresh the library after creating the reversed file
        refresh_success, refresh_message = refresh_library()
        if refresh_success:
            combined_message = f"Successfully created reversed file: {new_filename}. Library refreshed successfully."
        else:
            combined_message = f"Successfully created reversed file: {new_filename}. Library refresh failed: {refresh_message}"
        
        return True, combined_message
    except Exception as e:
        print(f"Error reversing file {filepath}: {e}")
        return False, f"Error reversing file {filename}: {e}"
