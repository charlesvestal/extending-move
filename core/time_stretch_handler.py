import os
import librosa
import soundfile as sf
import tempfile
import numpy as np
from audiotsm.io.array import ArrayReader, ArrayWriter
from audiotsm import wsola

from core.refresh_handler import refresh_library

def time_stretch_wav(input_path, target_duration, output_path, preserve_pitch=True, algorithm='wsola'):
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
        # Preserve original file format and subtype for writing (e.g., 24-bit WAV)
        info = sf.info(input_path)
        subtype = info.subtype
        # Determine format based on extension
        ext_lower = os.path.splitext(input_path)[1].lower()
        format_map = {
            '.wav': 'WAV',
            '.aif': 'AIFF',
            '.aiff': 'AIFF'
        }
        write_format = format_map.get(ext_lower)

        # Load audio
        y, sr = librosa.load(input_path, sr=None, mono=True)
        original_duration = librosa.get_duration(y=y, sr=sr)
        if original_duration == 0:
            return False, "Source file duration is zero", None

        # Compute stretch ratio
        rate = original_duration / target_duration
        if rate <= 0:
            return False, "Invalid target duration.", None

        if preserve_pitch:
            if algorithm == 'wsola':
                # Load audio data for WSOLA
                data, sr = sf.read(input_path, dtype='float32')
                # Ensure shape is (channels, frames)
                if data.ndim == 1:
                    data = data[np.newaxis, :]
                else:
                    data = data.T
                # Time-stretch using array-based WSOLA
                reader = ArrayReader(data)
                writer = ArrayWriter(data.shape[0])
                tsm = wsola(data.shape[0])
                tsm.set_speed(rate)
                tsm.run(reader, writer)
                # Retrieve stretched data
                y_stretched = writer.data
                # Convert back to (frames, channels) or 1D
                if y_stretched.shape[0] == 1:
                    y_stretched = y_stretched.flatten()
                else:
                    y_stretched = y_stretched.T
                # Write output preserving original format and subtype
                sf.write(
                    output_path,
                    y_stretched,
                    sr,
                    format=write_format,
                    subtype=subtype
                )
            elif algorithm == 'phase':
                # Phase-vocoder via librosa for smooth harmonic material
                y_stretched = librosa.effects.time_stretch(y, rate=rate)
                sf.write(
                    output_path,
                    y_stretched,
                    sr,
                    format=write_format,
                    subtype=subtype
                )
            else:
                return False, f"Unknown algorithm: {algorithm}", None
        else:
            # Repitch by adjusting sample rate
            new_sr = int(sr * rate)
            sf.write(
                output_path,
                y,
                new_sr,
                format=write_format,
                subtype=subtype
            )

        # Refresh library
        refresh_success, refresh_message = refresh_library()
        if refresh_success:
            msg = f"Stretched to {target_duration:.2f}s. Library refreshed."
        else:
            msg = f"Stretched to {target_duration:.2f}s. Library refresh failed: {refresh_message}"

        return True, msg, output_path
    except Exception as e:
        return False, f"Error stretching WAV: {e}", None