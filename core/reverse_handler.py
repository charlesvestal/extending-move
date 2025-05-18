import os
import wave
import numpy as np

from core.refresh_handler import refresh_library

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
    return wav_files

def reverse_wav_file(filename, directory):
    """
    Handles reversing and un-reversing WAV files.
    If the file ends with _reverse.wav or _reversed.wav, attempts to switch back.
    Otherwise, creates a reversed version, including manual 24-bit support.
    Returns (success: bool, message: str, new_path: str).
    """
    filepath = os.path.join(directory, filename)
    if not os.path.isfile(filepath):
        return False, f"File does not exist: {filepath}", None
        
    base, ext = os.path.splitext(filename)

    try:
        # --- handle toggling back to original ---
        if base.endswith('_reverse') or base.endswith('_reversed'):
            suffix_len = 8 if base.endswith('_reverse') else 9
            original_base = base[:-suffix_len]
            original_filename = f"{original_base}{ext}"
            original_filepath = os.path.join(directory, original_filename)
            if os.path.exists(original_filepath):
                return True, f"Switched to original file: {original_filename}", original_filepath
            else:
                return False, f"Original file not found: {original_filename}", None

        # --- create reversed version ---
        new_filename = f"{base}_reversed{ext}"
        new_filepath = os.path.join(directory, new_filename)
        if os.path.exists(new_filepath):
            return True, f"Using existing reversed file: {new_filename}", new_filepath

        with wave.open(filepath, 'rb') as wf:
            params = wf.getparams()
            n_channels, sampwidth, framerate, n_frames, comptype, compname = params
            frames = wf.readframes(n_frames)

        # --- unpack samples ---
        if sampwidth == 3:
            # 24-bit little-endian PCM → manual unpack to int32
            raw = np.frombuffer(frames, dtype=np.uint8)
            raw = raw.reshape(-1, n_channels, 3)
            # combine bytes: little-endian
            samples = (
                raw[:,:,0].astype(np.int32)
                | (raw[:,:,1].astype(np.int32) << 8)
                | (raw[:,:,2].astype(np.int32) << 16)
            )
            # sign-extend 24→32 bits
            sign_bit = 1 << 23
            samples = (samples ^ sign_bit) - sign_bit

            audio_data = samples  # shape: (n_frames, n_channels)

        else:
            # use numpy built-in for 8, 16, or 32 bits
            dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(sampwidth)
            if dtype is None:
                return False, f"Unsupported sample width: {sampwidth} bytes.", None
            audio_data = np.frombuffer(frames, dtype=dtype)
            if n_channels > 1:
                audio_data = audio_data.reshape(-1, n_channels)

        # --- reverse in time ---
        reversed_data = audio_data[::-1]

        # --- repack samples ---
        if sampwidth == 3:
            # pack int32 back into 3 bytes, little-endian
            # ensure values fit in signed 24-bit
            vals = reversed_data.astype(np.int32)
            # mask to unsigned 24-bit
            vals = np.bitwise_and(vals, 0xFFFFFF)
            b0 = (vals & 0xFF).astype(np.uint8)
            b1 = ((vals >> 8) & 0xFF).astype(np.uint8)
            b2 = ((vals >> 16) & 0xFF).astype(np.uint8)
            packed = np.stack([b0, b1, b2], axis=-1)  # shape (n_frames, n_channels, 3)
            raw_out = packed.reshape(-1, 3).flatten().tobytes()

        else:
            flat = reversed_data.reshape(-1)
            raw_out = flat.tobytes()

        # --- write reversed WAV ---
        with wave.open(new_filepath, 'wb') as wf:
            wf.setparams(params)
            wf.writeframes(raw_out)

        # Refresh library
        refresh_success, refresh_message = refresh_library()
        if refresh_success:
            msg = f"Successfully created reversed file: {new_filename}. Library refreshed."
        else:
            msg = f"Created reversed file: {new_filename}. Library refresh failed: {refresh_message}"

        return True, msg, new_filepath

    except Exception as e:
        return False, f"Error reversing file {filename}: {e}", None