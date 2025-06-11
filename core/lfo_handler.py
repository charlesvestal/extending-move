#!/usr/bin/env python3
"""Defaults for the LFO visualizer."""

from typing import Dict


def get_lfo_defaults() -> Dict[str, float | str]:
    """Return default values for the LFO visualizer."""
    return {
        "shape": "sine",
        "rate": 1.0,
        "offset": 0.0,
        "amount": 1.0,
        "attack": 0.0,
    }
