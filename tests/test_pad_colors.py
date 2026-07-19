import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.pad_colors import move_color_to_ui, rgb_string


def test_rgb_string_valid_and_invalid():
    assert rgb_string(1) == "rgb(255, 25, 23)"
    assert rgb_string(999) == ""


def test_move_zero_color_aliases_the_first_palette_color():
    assert move_color_to_ui(0) == 1
    assert move_color_to_ui(1) == 1
    assert move_color_to_ui(24) == 24
    assert move_color_to_ui(None) is None
