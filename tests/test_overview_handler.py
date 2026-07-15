import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers.overview_handler_class import OverviewHandler
import handlers.overview_handler_class as overview_module


def test_generate_pad_grid_html_uses_shared_grid(monkeypatch):
    monkeypatch.setattr(
        overview_module,
        "get_sets_data",
        lambda: {
            "sets": [
                {
                    "slot": 5,
                    "xattr_color": 3,
                    "color_id": 4,
                    "name": "Test Set",
                    "bpm": 120.0,
                    "camelot": "8B",
                }
            ],
            "current_slot": 5,
        },
    )

    html = OverviewHandler().generate_pad_grid_html()

    assert 'class="pad-grid view-only"' in html
    assert 'id="pad_6" name="overview_pad" value="6"' in html
    assert 'class="pad-cell occupied active"' in html
    assert 'Test Set' in html
    assert '120.0 BPM' in html


def test_generate_pad_grid_html_escapes_set_names(monkeypatch):
    malicious_name = '<img src=x onerror="alert(1)">'
    monkeypatch.setattr(
        overview_module,
        "get_sets_data",
        lambda: {
            "sets": [
                {
                    "slot": 5,
                    "xattr_color": 1,
                    "color_id": 1,
                    "name": malicious_name,
                    "bpm": 120.0,
                    "camelot": "8B",
                }
            ],
            "current_slot": None,
        },
    )

    html = OverviewHandler().generate_pad_grid_html()

    assert malicious_name not in html
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in html


def test_generate_pad_grid_html_restore_mode_selects_only_free_pads(monkeypatch):
    monkeypatch.setattr(
        overview_module,
        "get_sets_data",
        lambda: {
            "sets": [
                {
                    "slot": 5,
                    "xattr_color": 3,
                    "color_id": 4,
                    "name": "Test Set",
                    "bpm": 120.0,
                    "camelot": "8B",
                }
            ],
            "current_slot": 5,
        },
    )

    html = OverviewHandler().generate_pad_grid_html(restore_mode=True)

    assert 'class="pad-grid"' in html
    assert 'id="pad_6" name="overview_pad" value="6" disabled' in html
    assert 'id="pad_7" name="overview_pad" value="7" ' in html
