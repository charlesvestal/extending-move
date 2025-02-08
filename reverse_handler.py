import os
import wave
import contextlib

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
            frames = wf.readframes(params.nframes)
        
        # Reverse the frames
        reversed_frames = frames[::-1]
        
        with wave.open(filepath, 'wb') as wf:
            wf.setparams(params)
            wf.writeframes(reversed_frames)
        
        print(f"Successfully reversed the file: {filepath}")
        return True, f"Successfully reversed the file: {filename}"
    except Exception as e:
        print(f"Error reversing file {filepath}: {e}")
        return False, f"Error reversing file {filename}: {e}"
