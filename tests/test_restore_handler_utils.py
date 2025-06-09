import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers.restore_handler_class import RestoreHandler


def test_generate_pad_options_empty():
    h = RestoreHandler()
    html = h.generate_pad_options([])
    assert 'No pads available' in html


def test_generate_pad_options_some():
    h = RestoreHandler()
    html = h.generate_pad_options([2, 4])
    assert html.count('<option') == 2
    assert 'selected' in html.split('<option')[1]


def test_generate_pad_grid():
    h = RestoreHandler()
    html = h.generate_pad_grid({0, 31}, {0: 1})
    assert html.count('class="pad-cell occupied"') == 2
    assert 'restore_pad_1" name="mset_index" value="1" disabled' in html
    assert 'background-color: rgb(' in html

def test_generate_color_options_custom():
    h = RestoreHandler()
    html = h.generate_color_options("clr", "pad")
    assert 'id="clr_dropdown"' in html
    assert 'name="clr"' in html
    assert 'padName = "pad"' in html
    assert 'color-dropdown' in html
