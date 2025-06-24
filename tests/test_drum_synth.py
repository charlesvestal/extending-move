import os
from pathlib import Path
import numpy as np
import soundfile as sf

# ensure project root is in path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.drum_synth import synthesize_808_kick


def test_synthesize_808_kick(tmp_path):
    outp = tmp_path / "kick.wav"
    success, msg, path = synthesize_808_kick(str(outp), pitch_hz=60, length_beats=1)
    assert success, msg
    assert os.path.exists(path)
    data, sr = sf.read(path, dtype="float32")
    assert len(data) > 0
    length_sec = len(data) / sr
    assert 0.4 < length_sec < 0.6  # ~1 beat at 120 bpm
