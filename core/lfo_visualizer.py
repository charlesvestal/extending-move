#!/usr/bin/env python3
"""Utility functions for the LFO visualizer."""

from typing import Dict, Tuple, List
import numpy as np


def get_lfo_defaults() -> Dict[str, float | str]:
    """Return default LFO parameter values."""
    return {
        "shape": "sine",
        "rate": 1.0,
        "offset": 0.0,
        "amount": 1.0,
        "attack": 0.0,
    }


def compute_lfo_cycle(
    shape: str,
    rate: float,
    offset: float,
    amount: float,
    attack: float,
    duration: float = 1.0,
    n: int = 100,
) -> Tuple[List[float], List[float]]:
    """Generate an LFO cycle for visualization."""
    t = np.linspace(0.0, duration, n)
    phase = rate * t
    s = shape.lower()
    if s == "saw":
        base = 2 * (phase % 1) - 1
    elif s == "square":
        base = np.where((phase % 1) < 0.5, 1.0, -1.0)
    elif s == "triangle":
        base = 1 - 4 * np.abs(np.round(phase - 0.25) - (phase - 0.25))
    else:  # default to sine
        base = np.sin(2 * np.pi * phase)

    if attack > 0:
        env = np.clip(t / attack, 0.0, 1.0)
    else:
        env = 1.0
    y = offset + amount * env * base
    return t.tolist(), y.tolist()
