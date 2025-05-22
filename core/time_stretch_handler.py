import os
import librosa
import soundfile as sf

from core.refresh_handler import refresh_library

def time_stretch_wav(input_path, target_duration, output_path):
    """
    Time-stretch a WAV file to a target duration, keeping pitch constant.

    Args:
        input_path (str): Source WAV file path.
        target_duration (float): Desired output length in seconds.
        output_path (str): Path to save new file.

    Returns:
        tuple: (success: bool, message: str, output_path: str)
    """
    try:
        # Load audio
        y, sr = librosa.load(input_path, sr=None, mono=True)
        original_duration = librosa.get_duration(y=y, sr=sr)
        if original_duration == 0:
            return False, "Source file duration is zero", None

        # Compute stretch ratio
        rate = original_duration / target_duration
        if rate <= 0:
            return False, "Invalid target duration.", None

        # Stretch (preserves pitch)
        y_stretched = librosa.effects.time_stretch(y, rate=rate)

        # Write to output path (overwrite if exists)
        sf.write(output_path, y_stretched, sr)

        # Refresh library
        refresh_success, refresh_message = refresh_library()
        if refresh_success:
            msg = f"Stretched to {target_duration:.2f}s. Library refreshed."
        else:
            msg = f"Stretched to {target_duration:.2f}s. Library refresh failed: {refresh_message}"

        return True, msg, output_path
    except Exception as e:
        return False, f"Error stretching WAV: {e}", None