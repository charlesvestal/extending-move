import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from handlers import synth_param_editor_handler_class as speh
class SimpleForm(dict):
    def getvalue(self, name, default=None):
        return self.get(name, default)


def test_new_preset_triggers_refresh(monkeypatch, tmp_path):
    default_preset = tmp_path / "default.json"
    default_preset.write_text(json.dumps({"kind": "drift", "parameters": {}}))

    monkeypatch.setattr(speh, "DEFAULT_PRESET", str(default_preset))
    monkeypatch.setattr(speh, "NEW_PRESET_DIR", str(tmp_path))
    monkeypatch.setattr(speh, "CORE_LIBRARY_DIR", str(tmp_path / "core"))

    monkeypatch.setattr(speh, "generate_dir_html", lambda *a, **k: "")
    monkeypatch.setattr(speh, "load_drift_schema", lambda: {})
    monkeypatch.setattr(speh, "extract_parameter_values", lambda p: {"success": True, "parameters": []})
    monkeypatch.setattr(speh, "extract_macro_information", lambda p: {"success": True, "macros": [], "mapped_parameters": {}})
    monkeypatch.setattr(speh, "extract_available_parameters", lambda p: {"success": True, "parameters": [], "parameter_paths": {}})

    called = {}
    def fake_refresh():
        called['done'] = True
        return True, "ok"
    monkeypatch.setattr(speh, "refresh_library", fake_refresh)

    handler = speh.SynthParamEditorHandler()
    form = SimpleForm({'action': 'new_preset', 'new_preset_name': 'Test'})
    result = handler.handle_post(form)

    assert called.get('done') is True
    assert "Library refreshed" in result['message']
    assert (tmp_path / "Test.ablpreset").exists()
