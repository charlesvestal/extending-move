#!/usr/bin/env python3
"""Simple drum synthesis utilities."""

from typing import Tuple
import numpy as np
import soundfile as sf


def synthesize_808_kick(
    output_path: str,
    pitch_hz: float = 50.0,
    length_beats: float = 1.0,
    tempo: float = 120.0,
    sr: int = 44100,
) -> Tuple[bool, str, str]:
    """Synthesize an 808-style kick drum.

    Args:
        output_path: Destination WAV path.
        pitch_hz: Base pitch in Hz controlled by knob A.
        length_beats: Duration in beats controlled by knob B.
        tempo: Tempo in BPM to convert beats to seconds.
        sr: Sample rate.

    Returns:
        Tuple of success, message and output path.
    """
    try:
        if length_beats <= 0:
            return False, "length_beats must be positive", output_path

        length_sec = (60.0 / tempo) * length_beats
        n_samples = int(sr * length_sec)
        if n_samples <= 0:
            return False, "length too short", output_path

        t = np.linspace(0, length_sec, n_samples, endpoint=False)

        # Exponential frequency drop similar to 808
        f_start = pitch_hz * 2.0
        freq = f_start * np.exp(-t * 8) + pitch_hz
        phase = 2 * np.pi * np.cumsum(freq) / sr

        # Amplitude envelope: long decay
        amp = np.exp(-t * 4)

        # Add short click at the start
        click = np.exp(-t * 50)
        wave = amp * np.sin(phase) + 0.01 * click * np.random.randn(n_samples)

        sf.write(output_path, wave.astype(np.float32), sr)
        return True, "Kick synthesized", output_path
    except Exception as exc:
        return False, f"Error synthesizing kick: {exc}", output_path
