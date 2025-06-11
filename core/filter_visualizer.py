import numpy as np
from scipy import signal


def _biquad_coeffs(filter_type: str, freq: float, q: float, sr: int = 44100):
    """Return biquad filter coefficients."""
    w0 = 2 * np.pi * freq / sr
    alpha = np.sin(w0) / (2 * q)
    cosw0 = np.cos(w0)

    f = filter_type.lower()
    if f == "lowpass":
        b0 = (1 - cosw0) / 2
        b1 = 1 - cosw0
        b2 = (1 - cosw0) / 2
        a0 = 1 + alpha
        a1 = -2 * cosw0
        a2 = 1 - alpha
    elif f == "highpass":
        b0 = (1 + cosw0) / 2
        b1 = -(1 + cosw0)
        b2 = (1 + cosw0) / 2
        a0 = 1 + alpha
        a1 = -2 * cosw0
        a2 = 1 - alpha
    elif f == "bandpass":
        b0 = alpha
        b1 = 0
        b2 = -alpha
        a0 = 1 + alpha
        a1 = -2 * cosw0
        a2 = 1 - alpha
    elif f == "notch":
        b0 = 1
        b1 = -2 * cosw0
        b2 = 1
        a0 = 1 + alpha
        a1 = -2 * cosw0
        a2 = 1 - alpha
    else:  # default to lowpass
        b0 = (1 - cosw0) / 2
        b1 = 1 - cosw0
        b2 = (1 - cosw0) / 2
        a0 = 1 + alpha
        a1 = -2 * cosw0
        a2 = 1 - alpha

    b = np.array([b0, b1, b2]) / a0
    a = np.array([1, a1 / a0, a2 / a0])
    return b, a


def _single_response(
    filter_type: str,
    cutoff: float,
    q: float,
    slope: str,
    sr: int,
    freqs: np.ndarray,
):
    """Return magnitude response for a single biquad type."""
    b, a = _biquad_coeffs(filter_type, cutoff, q, sr)
    w = 2 * np.pi * freqs / sr
    w, h = signal.freqz(b, a, worN=w)
    if str(slope) == "24":
        _, h2 = signal.freqz(b, a, worN=w)
        h *= h2
    mag = 20 * np.log10(np.abs(h) + 1e-9)
    return mag


def compute_filter_response(
    filter_type: str,
    cutoff: float,
    resonance: float,
    slope: str,
    sr: int = 44100,
    n: int = 512,
    morph: float = 0.0,
):
    """Compute frequency response for a single filter."""
    freqs = np.logspace(np.log10(10), np.log10(20000), n)
    q = 0.5 + 9.5 * resonance

    if filter_type.lower() == "morph":
        stages = ["lowpass", "bandpass", "highpass", "notch", "lowpass"]
        pos = morph * 4
        idx = int(np.floor(pos))
        frac = pos - idx
        mag1 = _single_response(stages[idx], cutoff, q, slope, sr, freqs)
        mag2 = _single_response(stages[idx + 1], cutoff, q, slope, sr, freqs)
        mag = mag1 * (1 - frac) + mag2 * frac
    else:
        mag = _single_response(filter_type, cutoff, q, slope, sr, freqs)

    return freqs.tolist(), mag.tolist()


def compute_chain_response(
    filter1: dict,
    filter2: dict | None = None,
    routing: str = "Serial",
    sr: int = 44100,
    n: int = 512,
):
    """Compute frequency response for one or two filters."""
    f1_w, f1_mag = compute_filter_response(**filter1, sr=sr, n=n)
    if not filter2:
        return f1_w, f1_mag

    _, f2_mag = compute_filter_response(**filter2, sr=sr, n=n)

    if routing.lower() == "serial":
        h1 = 10 ** (np.array(f1_mag) / 20)
        h2 = 10 ** (np.array(f2_mag) / 20)
        h = h1 * h2
        mag = 20 * np.log10(np.abs(h) + 1e-9)
        return f1_w, mag.tolist()

    # For parallel or split, return both magnitudes separately
    return f1_w, f1_mag, f2_mag
