#!/usr/bin/env python3
"""Utility functions for the Cycling Envelope visualizer prototype."""

from typing import Dict


def get_cycling_env_defaults() -> Dict[str, float | str]:
    """Return default values for the Cycling Envelope visualizer."""
    return {
        "rate": 2.0,  # Hz
        "tilt": 0.0,
        "hold": 0.0,
        "time_mode": "Hz",
    }
