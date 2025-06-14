#!/usr/bin/env python3
"""Utilities for the Clip Editor prototype."""

from typing import Dict, List


def get_default_clip() -> Dict[str, List[Dict[str, float]] | float | str]:
    """Return a simple default clip with a few notes."""
    notes = [
        {"id": 1, "pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100},
        {"id": 2, "pitch": 64, "start": 1.0, "duration": 1.0, "velocity": 100},
        {"id": 3, "pitch": 67, "start": 2.0, "duration": 1.0, "velocity": 100},
    ]
    return {
        "notes": notes,
        "region": 4.0,
        "message": "Use the canvas to edit notes",
        "message_type": "info",
    }

