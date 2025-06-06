#!/usr/bin/env python3
"""Utility script to populate free pads with sets of sequential colors.

This script restores a dummy Ableton set to each available pad, assigning
colors incrementally within a specified range. It is useful for mapping the
numerical color IDs displayed on the device.
"""

import argparse
import os
import shutil
import tempfile
import zipfile

from core.list_msets_handler import list_msets_free
from core.restore_handler import restore_ablbundle
from core.config import MSET_COLOR_RANGE

EXAMPLE_SET = os.path.join(
    os.path.dirname(__file__), '..', 'examples', 'Sets', 'midi_template.abl'
)


def create_dummy_bundle() -> str:
    """Create a temporary .ablbundle based on the example set.

    Returns:
        Path to the created bundle file.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        song_path = os.path.join(temp_dir, 'Song.abl')
        shutil.copy(EXAMPLE_SET, song_path)
        fd, bundle_path = tempfile.mkstemp(suffix='.ablbundle')
        os.close(fd)
        with zipfile.ZipFile(bundle_path, 'w') as zf:
            zf.write(song_path, arcname='Song.abl')
        return bundle_path
    finally:
        shutil.rmtree(temp_dir)


def main(start_color: int, end_color: int) -> None:
    if start_color < MSET_COLOR_RANGE[0] or end_color > MSET_COLOR_RANGE[1]:
        raise ValueError(
            f"Color range must be within {MSET_COLOR_RANGE[0]}-"
            f"{MSET_COLOR_RANGE[1]}"
        )
    if start_color > end_color:
        raise ValueError('start_color must be <= end_color')

    free_pads = list_msets_free()
    if not free_pads:
        print('No free pads available')
        return

    bundle = create_dummy_bundle()
    try:
        colors = list(range(start_color, end_color + 1))
        for pad, color in zip(free_pads, colors):
            result = restore_ablbundle(bundle, pad, color)
            status = 'OK' if result.get('success') else 'FAIL'
            print(f"Pad {pad} -> Color {color}: {status} - {result.get('message')}")
    finally:
        os.remove(bundle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Populate pads with color tests.')
    parser.add_argument('--start-color', type=int, default=MSET_COLOR_RANGE[0])
    parser.add_argument('--end-color', type=int, default=MSET_COLOR_RANGE[1])
    args = parser.parse_args()
    main(args.start_color, args.end_color)
