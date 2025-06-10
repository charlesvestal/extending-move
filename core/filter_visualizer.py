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


def compute_filter_response(filter_type: str, cutoff: float, resonance: float, slope: str, sr: int = 44100, n: int = 512):
    """Compute frequency response for a single filter."""
    q = 0.5 + 9.5 * resonance
    b, a = _biquad_coeffs(filter_type, cutoff, q, sr)
    w, h = signal.freqz(b, a, n, fs=sr)
    if str(slope) == "24":
        w2, h2 = signal.freqz(b, a, n, fs=sr)
        h *= h2
    mag = 20 * np.log10(np.abs(h) + 1e-9)
    return w.tolist(), mag.tolist()


def compute_chain_response(filter1: dict, filter2: dict | None = None, routing: str = "Serial", sr: int = 44100, n: int = 512):
    """Compute frequency response for two filters combined."""
    f1_w, f1_mag = compute_filter_response(**filter1, sr=sr, n=n)
    if not filter2:
        return f1_w, f1_mag
    f2_w, f2_mag = compute_filter_response(**filter2, sr=sr, n=n)
    h1 = 10 ** (np.array(f1_mag) / 20)
    h2 = 10 ** (np.array(f2_mag) / 20)
    if routing.lower() == "serial":
        h = h1 * h2
    else:  # parallel or split
        h = 0.5 * (h1 + h2)
    mag = 20 * np.log10(np.abs(h) + 1e-9)
    return f1_w, mag.tolist()
