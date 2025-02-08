import os
import wave
import numpy as np

def get_wav_files(directory="/data/UserData/UserLibrary/Samples"):
    """
    Retrieves a list of WAV files from the specified directory.
    """
    if not os.path.isdir(directory):
        print(f"Directory does not exist: {directory}")
        return []
    
    wav_files = [f for f in os.listdir(directory) if f.lower().endswith('.wav') and os.path.isfile(os.path.join(directory, f))]
    return wav_files

def reverse_wav_file(filename, directory="/data/UserData/UserLibrary/Samples"):
    """
    Reverses the WAV file specified by filename in the given directory.
    Overwrites the original file with its reversed version.
    Returns a tuple (success: bool, message: str).
    """
    filepath = os.path.join(directory, filename)
    
    if not os.path.isfile(filepath):
        return False, f"File does not exist: {filepath}"
    
    try:
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
        
        # Write the reversed frames back to the WAV file
        with wave.open(filepath, 'wb') as wf:
            wf.setparams(params)
            wf.writeframes(reversed_frames)
        
        print(f"Successfully reversed the file: {filepath}")
        return True, f"Successfully reversed the file: {filename}"
    except Exception as e:
        print(f"Error reversing file {filepath}: {e}")
        return False, f"Error reversing file {filename}: {e}"
