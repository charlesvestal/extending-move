import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.lfo_visualizer import compute_lfo_cycle


def test_sine_cycle():
    t, y = compute_lfo_cycle('sine', 1.0, 0.0, 1.0, 0.0, n=5, duration=1.0)
    assert len(t) == 5 and len(y) == 5
    # quarter cycle at index 1 (~0.25s)
    assert abs(y[1] - 1.0) < 1e-6
    # half cycle should return near 0
    assert abs(y[2]) < 1e-6


def test_attack_scaling():
    _, y = compute_lfo_cycle('sine', 1.0, 0.0, 1.0, 0.5, n=3, duration=0.5)
    # final value should have reached full amplitude
    assert abs(y[-1]) > abs(y[0])
