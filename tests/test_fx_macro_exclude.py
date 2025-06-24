import json
from pathlib import Path

from handlers import fx_chain_editor_handler_class as fceh
from core.fx_chain_handler import extract_fx_parameters


class SimpleForm(dict):
    def getvalue(self, name, default=None):
        return self.get(name, default)


def create_fx_preset(path: Path) -> None:
    preset = {
        "kind": "delay",
        "parameters": {
            "Volume": 0.5,
            "DelayLine_CompatibilityMode": 1,
            "DryWetMode": 0,
            "EcoProcessing": True,
            "Enabled": True,
            "Oversampling": 2,
            "HiQuality": True,
            "HostVisualisationRate": 0.5,
            "InternalSideChainGain": 0.0,
            "SideChainListen": False,
            "SideChainMono": False,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(preset))


def test_excluded_macro_params(monkeypatch, tmp_path):
    p = tmp_path / "Delay" / "effect.json"
    create_fx_preset(p)

    monkeypatch.setattr(fceh, "refresh_library", lambda: (True, "ok"))
    monkeypatch.setattr(fceh, "generate_dir_html", lambda *a, **k: "")

    handler = fceh.FxChainEditorHandler()
    form = SimpleForm({"action": "select_preset", "preset_select": str(p)})
    result = handler.handle_post(form)

    params = json.loads(result["available_params_json"])
    for name in fceh.EXCLUDED_MACRO_PARAMS["Delay"]:
        assert name not in params

    info = extract_fx_parameters(str(p))
    names = [param["name"] for param in info["parameters"]]
    for name in fceh.EXCLUDED_MACRO_PARAMS["Delay"]:
        assert name in names
