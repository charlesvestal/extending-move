import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.pad_colors import rgb_string


def test_rgb_string_valid_and_invalid():
    assert rgb_string(1) == "rgb(255, 25, 23)"
    assert rgb_string(999) == ""
