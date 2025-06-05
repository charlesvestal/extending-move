import os
import numpy as np
import soundfile as sf
import librosa

def load_mono(path):
    data, sr = sf.read(path, dtype='float32')
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    return data, sr

def active_duration(y, sr, threshold=1e-4):
    idx = np.where(np.abs(y) > threshold)[0]
    if len(idx) == 0:
        return 0.0
    return (idx[-1] - idx[0]) / sr

def active_bounds(y, sr, threshold=1e-4):
    idx = np.where(np.abs(y) > threshold)[0]
    if len(idx) == 0:
        return 0.0, 0.0
    return idx[0] / sr, idx[-1] / sr

def generate_chord(y, sr, intervals):
    buffers = []
    for semitone in intervals:
        shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitone)
        shifted = librosa.util.fix_length(shifted, size=len(y))
        buffers.append(shifted)
    mix = np.sum(buffers, axis=0) / len(buffers)
    return mix

def test_examples_have_equal_length():
    paths = [
        'examples/Samples/010 Pizz Str.wav',
        'examples/Samples/organ.wav',
    ]
    intervals = [0, 4, 7]
    for p in paths:
        y, sr = load_mono(p)
        orig_dur = active_duration(y, sr)
        orig_start, orig_end = active_bounds(y, sr)
        chord = generate_chord(y, sr, intervals)
        assert len(chord) == len(y)
        chord_dur = active_duration(chord, sr)
        chord_start, chord_end = active_bounds(chord, sr)
        assert abs(chord_dur - orig_dur) < 0.01
        assert abs(chord_start - orig_start) < 0.01
        assert abs(chord_end - orig_end) < 0.01
