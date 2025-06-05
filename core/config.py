"""Configuration constants for Move server paths and allowed ranges.

This module centralizes the absolute paths used when working with Move
sets and samples on the device. It also defines the valid numeric ranges
accepted from users when restoring a set.  All ranges are inclusive.
"""

# Path where Move sets are stored.  Each restored set is placed in a
# unique UUID-named folder beneath this directory.
MSETS_DIRECTORY = "/data/UserData/UserLibrary/Sets"

# Root directory of the sample library.  When rewriting sample references
# inside a restored set, paths are redirected here.
MSET_SAMPLE_PATH = "/data/UserData/UserLibrary/Samples"

# Base URI prefix inserted into Song.abl files to reference set contents.
MSET_ABLETON_URI = "ableton:/user-library/Sets"

# Inclusive range of valid pad indices (0–31).
MSET_INDEX_RANGE = (0, 31)

# Inclusive range of valid color IDs used by Move's UI (1–26).
MSET_COLOR_RANGE = (1, 26)
