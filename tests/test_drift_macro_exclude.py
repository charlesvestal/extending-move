import json
from pathlib import Path

from handlers import synth_param_editor_handler_class as speh

class SimpleForm(dict):
    def getvalue(self, name, default=None):
        return self.get(name, default)


def create_drift_preset(path):
    preset = {
        "kind": "instrumentRack",
        "chains": [
            {"devices": [{"kind": "drift", "parameters": {"Volume": 0.5}}]}
        ],
    }
    Path(path).write_text(json.dumps(preset))


def test_excluded_macro_params(monkeypatch, tmp_path):
    p = tmp_path / "preset.ablpreset"
    create_drift_preset(p)
    monkeypatch.setattr(speh, "refresh_library", lambda: (True, "ok"))
    monkeypatch.setattr(speh, "generate_dir_html", lambda *a, **k: "")

    handler = speh.SynthParamEditorHandler()
    form = SimpleForm({"action": "select_preset", "preset_select": str(p)})
    result = handler.handle_post(form)

    params = json.loads(result["available_params_json"])
    for name in speh.EXCLUDED_MACRO_PARAMS:
        assert name not in params
