import numpy as np
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from core.filter_visualizer import compute_filter_response, compute_chain_response


def test_log_scale_output():
    freq, mag = compute_filter_response('lowpass', 1000, 0.0, '12', n=8)
    assert freq[0] >= 9
    assert freq[-1] <= 20001
    ratios = [freq[i+1]/freq[i] for i in range(len(freq)-1)]
    first_ratio = ratios[0]
    for r in ratios[1:]:
        assert abs(r - first_ratio) < 1e-3


def test_morph_matches_endpoints():
    freq_lp, mag_lp = compute_filter_response('lowpass', 1000, 0.0, '12', n=32)
    freq_m, mag_m = compute_filter_response('Morph', 1000, 0.0, '12', n=32, morph=0.0)
    assert np.allclose(mag_lp, mag_m, atol=1e-6)
    freq_hp, mag_hp = compute_filter_response('highpass', 1000, 0.0, '12', n=32)
    freq_m2, mag_m2 = compute_filter_response('Morph', 1000, 0.0, '12', n=32, morph=0.5)
    assert np.allclose(mag_hp, mag_m2, atol=1e-6)


def test_chain_serial():
    f1 = {'filter_type': 'lowpass', 'cutoff': 500, 'resonance': 0.0, 'slope': '12'}
    f2 = {'filter_type': 'highpass', 'cutoff': 2000, 'resonance': 0.0, 'slope': '12'}
    freq, mag = compute_chain_response(f1, f2, 'Serial', n=16)
    freq1, mag1 = compute_filter_response(**f1, n=16)
    freq2, mag2 = compute_filter_response(**f2, n=16)
    expected = 20 * np.log10((10**(np.array(mag1)/20)) * (10**(np.array(mag2)/20)) + 1e-9)
    assert np.allclose(mag, expected)
