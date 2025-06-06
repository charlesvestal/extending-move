import os
from pathlib import Path
import soundfile as sf
import pyrubberband.pyrb as pyrb
import librosa
import numpy as np
from audiotsm.io.array import ArrayReader, ArrayWriter
from audiotsm import wsola

from core.refresh_handler import refresh_library


def pitch_shift_array(data, sr, semitones):
    """Pitch-shift audio using Rubber Band while preserving length."""
    rb_binary = Path(__file__).resolve().parents[1] / 'bin' / 'rubberband' / 'rubberband'
    pyrb.__RUBBERBAND_UTIL = str(rb_binary)
    return pyrb.pitch_shift(data, sr, semitones)

def time_stretch_wav(
    input_path,
    target_duration,
    output_path,
    preserve_pitch=True,
    algorithm='rubberband',
):
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
            if algorithm == 'rubberband':
                rb_binary = Path(__file__).resolve().parents[1] / 'bin' / 'rubberband' / 'rubberband'
                pyrb.__RUBBERBAND_UTIL = str(rb_binary)
                try:
                    y_stretched = pyrb.time_stretch(y, sr, rate)
                except Exception:
                    if y.ndim > 1:
                        y_mono = np.mean(y, axis=1)
                    else:
                        y_mono = y
                    y_stretched = librosa.effects.time_stretch(y_mono, rate=rate)
                sf.write(output_path, y_stretched, sr, format=write_format, subtype=subtype)
            elif algorithm == 'wsola':
                data = y if y.ndim == 1 else y.T
                if data.ndim == 1:
                    data = data[np.newaxis, :]
                reader = ArrayReader(data)
                writer = ArrayWriter(data.shape[0])
                tsm = wsola(data.shape[0])
                tsm.set_speed(rate)
                tsm.run(reader, writer)
                y_stretched = writer.data
                y_stretched = y_stretched.flatten() if y_stretched.shape[0] == 1 else y_stretched.T
                sf.write(output_path, y_stretched, sr, format=write_format, subtype=subtype)
            elif algorithm == 'phase':
                if y.ndim > 1:
                    y_mono = np.mean(y, axis=1)
                else:
                    y_mono = y
                y_stretched = librosa.effects.time_stretch(y_mono, rate=rate)
                sf.write(output_path, y_stretched, sr, format=write_format, subtype=subtype)
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