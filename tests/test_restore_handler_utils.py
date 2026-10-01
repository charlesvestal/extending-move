import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers.restore_handler_class import RestoreHandler
from handlers.overview_handler_class import OverviewHandler
import handlers.overview_handler_class as overview_module


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
    html = h.generate_pad_grid({0, 31}, {0: 1}, input_name="mset_index", free_only=True)
    assert html.count('class="pad-cell occupied"') == 2
    assert 'id="pad_1" name="mset_index" value="1" disabled' in html
    assert 'background-color: rgba(' in html

def test_generate_color_options_custom():
    h = RestoreHandler()
    html = h.generate_color_options("clr", "pad")
    assert 'id="clr_dropdown"' in html
    assert 'name="clr"' in html
    assert 'padName = "pad"' in html
    assert 'color-dropdown' in html


def test_overview_restore_message_uses_ui_pad_number(monkeypatch, tmp_path):
    class Form(dict):
        def getvalue(self, name, default=None):
            return self.get(name, default)

    upload_path = tmp_path / "test.abl"
    upload_path.write_text("{}")
    handler = OverviewHandler()
    monkeypatch.setattr(
        handler,
        "handle_file_upload",
        lambda form, field_name: (True, str(upload_path), None),
    )
    monkeypatch.setattr(
        overview_module,
        "restore_abl",
        lambda filepath, pad, color: {
            "success": True,
            "message": f"Successfully restored test to pad {pad}",
        },
    )

    result = handler.handle_post_restore(
        Form({"target_pad": "6", "pad_color": "1"})
    )

    assert result["success"]
    assert result["message"] == "Successfully restored test to pad 6"
