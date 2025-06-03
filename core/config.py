# config.py

"""Configuration helpers for file paths.

This module resolves the directories used by the webserver. When running on the
Move hardware the paths under ``/data/UserData`` exist. For local development we
fall back to the ``examples`` directory so the code can run without the device.

Environment variables may override any of these locations:

``MSETS_DIRECTORY``      Path to the Sets directory
``MSET_SAMPLE_PATH``     Path to the Samples directory
``TRACK_PRESET_DIR``     Path to the Track Presets directory
"""

import os


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def _resolve_path(env_name: str, default_path: str, example_subdir: str) -> str:
    """Return a usable path for Move data or the examples fallback."""

    if env_name in os.environ:
        return os.environ[env_name]
    if os.path.exists(default_path):
        return default_path
    return os.path.join(EXAMPLES_DIR, example_subdir)


MSETS_DIRECTORY = _resolve_path(
    "MSETS_DIRECTORY",
    "/data/UserData/UserLibrary/Sets",
    "Sets",
)

MSET_SAMPLE_PATH = _resolve_path(
    "MSET_SAMPLE_PATH",
    "/data/UserData/UserLibrary/Samples",
    "Samples",
)

TRACK_PRESET_DIR = _resolve_path(
    "TRACK_PRESET_DIR",
    "/data/UserData/UserLibrary/Track Presets",
    "Track Presets",
)

SAMPLES_PRESET_DIR = os.path.join(MSET_SAMPLE_PATH, "Preset Samples")

MSET_ABLETON_URI = "ableton:/user-library/Sets"

# Allowed ranges for user inputs
MSET_INDEX_RANGE = (0, 31)  # Slot IDs
MSET_COLOR_RANGE = (1, 26)  # Color values
