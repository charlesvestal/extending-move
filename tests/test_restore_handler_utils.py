import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers.base_handler import BaseHandler
from handlers.overview_handler_class import OverviewHandler
import handlers.overview_handler_class as overview_module


def test_generate_pad_grid():
    h = BaseHandler()
    html = h.generate_pad_grid({0, 31}, {0: 1}, input_name="mset_index", free_only=True)
    assert html.count('class="pad-cell occupied"') == 2
    assert 'id="pad_1" name="mset_index" value="1" disabled' in html
    assert 'background-color: rgba(' in html


class Form(dict):
    def getvalue(self, name, default=None):
        return self.get(name, default)


def _overview_handler(monkeypatch, tmp_path, free=range(32)):
    upload_path = tmp_path / "test.abl"
    upload_path.write_text("{}")
    handler = OverviewHandler()
    monkeypatch.setattr(
        handler,
        "handle_file_upload",
        lambda form, field_name: (True, str(upload_path), None),
    )
    monkeypatch.setattr(overview_module, "list_msets_free", lambda: list(free))
    return handler


def test_overview_restore_reports_ui_pad_numbers(monkeypatch, tmp_path):
    def fail(*args):
        raise AssertionError("restore should not run")

    monkeypatch.setattr(overview_module, "restore_abl", fail)
    handler = _overview_handler(monkeypatch, tmp_path, free=[i for i in range(32) if i != 5])

    result = handler.handle_post_restore(Form({"target_pad": "6", "pad_color": "1"}))
    assert result == {"success": False, "message": "Pad 6 is already in use."}

    result = handler.handle_post_restore(Form({"target_pad": "33", "pad_color": "1"}))
    assert result["message"] == "Invalid pad 33. Must be between 1 and 32."

    result = handler.handle_post_restore(Form({"target_pad": "7", "pad_color": "26"}))
    assert result["message"] == "Invalid pad color 26. Must be between 1 and 25."


def test_overview_restore_message_uses_ui_pad_number(monkeypatch, tmp_path):
    handler = _overview_handler(monkeypatch, tmp_path)
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
