#!/usr/bin/env python3
"""Defaults for the cyclic envelope visualizer."""

from typing import Dict


def get_cyc_env_defaults() -> Dict[str, float]:
    """Return default values for the cyclic envelope."""
    return {
        "time": 1.0,
        "tilt": 0.5,
        "hold": 0.0,
    }
