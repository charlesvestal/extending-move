#!/usr/bin/env python3
"""Utility functions for the ADSR envelope visualizer."""

from typing import Dict


def get_adsr_defaults() -> Dict[str, float]:
    """Return default ADSR values for the prototype."""
    return {
        "attack": 0.2,
        "decay": 0.2,
        "sustain": 0.7,
        "release": 0.3,
    }
