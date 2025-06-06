import os
from pathlib import Path
import soundfile as sf
import pyrubberband.pyrb as pyrb
import librosa
import numpy as np

from core.refresh_handler import refresh_library

def time_stretch_wav(input_path, target_duration, output_path, preserve_pitch=True, algorithm='rubberband'):
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

        # Load audio (preserve channels)
        y, sr = sf.read(input_path, dtype='float32')
        if y.size == 0:
            return False, "Source file duration is zero", None
        if y.ndim == 1:
            original_duration = len(y) / sr
        else:
            original_duration = y.shape[0] / sr

        # Compute stretch ratio
        rate = original_duration / target_duration
        if rate <= 0:
            return False, "Invalid target duration.", None

        if preserve_pitch:
            rb_binary = Path(__file__).resolve().parents[1] / 'bin' / 'rubberband' / 'rubberband'
            pyrb.__RUBBERBAND_UTIL = str(rb_binary)
            try:
                # Use pyrubberband for high-quality time stretching
                y_stretched = pyrb.time_stretch(y, sr, rate)
            except Exception:
                # Fallback to librosa if rubberband fails
                if y.ndim > 1:
                    y_mono = np.mean(y, axis=1)
                else:
                    y_mono = y
                y_stretched = librosa.effects.time_stretch(y_mono, rate=rate)
            sf.write(
                output_path,
                y_stretched,
                sr,
                format=write_format,
                subtype=subtype
            )
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