#!/usr/bin/env python3
import os
import json

from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.fx_chain_handler import (
    extract_fx_parameters,
    save_fx_chain_with_macros,
)
from core.synth_preset_inspector_handler import extract_macro_information
from core.refresh_handler import refresh_library

CORE_LIBRARY_DIR = "/data/CoreLibrary/Audio Effects"
USER_LIBRARY_DIR = "/data/UserData/UserLibrary/Audio Effects"
if not os.path.exists(USER_LIBRARY_DIR) and os.path.exists("examples/Audio Effects"):
    USER_LIBRARY_DIR = "examples/Audio Effects"


class FxChainEditorHandler(BaseHandler):
    def handle_get(self):
        browser_html = generate_dir_html(
            USER_LIBRARY_DIR,
            "",
            "/fx-chain",
            "preset_select",
            "select_preset",
            filter_key="audiofx",
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith("</ul>"):
            browser_html = browser_html[:-5] + core_li + "</ul>"
        return {
            "message": "Select an effect preset or chain",
            "message_type": "info",
            "file_browser_html": browser_html,
            "params_html": "",
            "selected_preset": None,
            "browser_root": USER_LIBRARY_DIR,
            "browser_filter": "audiofx",
            "macro_knobs_html": "",
            "macros_json": "[]",
            "available_params_json": "[]",
            "param_paths_json": "{}",
            "param_count": 0,
            "new_preset_name": "",
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        if action == "reset_preset":
            return self.handle_get()

        preset_path = form.getvalue("preset_select")
        if not preset_path:
            return self.format_error_response("No preset selected")

        message = ""
        if action == "save_chain":
            macros_data_str = form.getvalue("macros_data") or "[]"
            try:
                macros = json.loads(macros_data_str)
            except Exception:
                macros = []
            try:
                count = int(form.getvalue("param_count", "0"))
            except ValueError:
                count = 0
            param_updates = {}
            for i in range(count):
                n = form.getvalue(f"param_{i}_name")
                v = form.getvalue(f"param_{i}_value")
                if n is not None and v is not None:
                    param_updates[n] = v
            new_name = form.getvalue("new_preset_name")
            if not new_name:
                new_name = os.path.basename(preset_path)
            if not new_name.endswith(".ablpreset") and not new_name.endswith(".json"):
                new_name += ".ablpreset"
            output_path = os.path.join(USER_LIBRARY_DIR, new_name)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result = save_fx_chain_with_macros(
                preset_path,
                macros,
                output_path,
                param_updates=param_updates,
            )
            if not result["success"]:
                return self.format_error_response(result["message"])
            refresh_success, refresh_message = refresh_library()
            message = result["message"]
            if refresh_success:
                message += " Library refreshed."
            else:
                message += f" Library refresh failed: {refresh_message}"
            preset_path = output_path
        elif action == "select_preset":
            message = f"Selected preset: {os.path.basename(preset_path)}"
        else:
            return self.format_error_response("Unknown action")

        param_info = extract_fx_parameters(preset_path)
        params_html = ""
        available_params_json = "[]"
        param_paths_json = "{}"
        if param_info["success"]:
            mapped_info = {}
            macro_info = extract_macro_information(preset_path)
            if macro_info["success"]:
                mapped_info = macro_info.get("mapped_parameters", {})
                macro_knobs_html = self.generate_macro_knobs_html(macro_info["macros"])
                macros_json = json.dumps(macro_info["macros"])
            else:
                macro_knobs_html = ""
                macros_json = "[]"
            params_html = self.generate_params_html(param_info["parameters"], mapped_info)
            available_params_json = json.dumps([p["name"] for p in param_info["parameters"]])
            param_paths_json = json.dumps(param_info.get("parameter_paths", {}))
            param_count = len(param_info["parameters"])
        else:
            macro_info = extract_macro_information(preset_path)
            macro_knobs_html = self.generate_macro_knobs_html(macro_info.get("macros", []))
            macros_json = json.dumps(macro_info.get("macros", []))
            param_count = 0

        browser_html = generate_dir_html(
            USER_LIBRARY_DIR,
            "",
            "/fx-chain",
            "preset_select",
            "select_preset",
            filter_key="audiofx",
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith("</ul>"):
            browser_html = browser_html[:-5] + core_li + "</ul>"
        return {
            "message": message,
            "message_type": "success",
            "file_browser_html": browser_html,
            "params_html": params_html,
            "selected_preset": preset_path,
            "browser_root": USER_LIBRARY_DIR,
            "browser_filter": "audiofx",
            "macro_knobs_html": macro_knobs_html,
            "macros_json": macros_json,
            "available_params_json": available_params_json,
            "param_paths_json": param_paths_json,
            "param_count": param_count,
            "new_preset_name": os.path.basename(preset_path),
        }

    def generate_params_html(self, params, mapped):
        html = []
        for i, p in enumerate(params):
            name = p.get("name")
            value = p.get("value")
            cls = "param-item"
            if name in mapped:
                cls += f" param-mapped macro-{mapped[name]['macro_index']}"
            html.append(
                f'<div class="{cls}" data-name="{name}">'
                f'<label>{name}: '
                f'<input type="text" name="param_{i}_value" value="{value}"></label>'
                f'<input type="hidden" name="param_{i}_name" value="{name}">'
                f'</div>'
            )
        return "".join(html)

    def generate_macro_knobs_html(self, macros):
        if not macros:
            macros = []
        by_index = {m["index"]: m for m in macros}
        html = ['<div class="macro-knob-row">']
        for i in range(8):
            info = by_index.get(i, {"name": f"Macro {i}", "value": 0.0})
            name = info.get("name", f"Macro {i}")
            label_class = ""
            if not name or name == f"Macro {i}":
                params = info.get("parameters") or []
                if len(params) == 1:
                    pname = params[0].get("name", f"Knob {i + 1}")
                    name = pname
                    label_class = " placeholder"
                else:
                    name = f"Knob {i + 1}"
            val = info.get("value", 0.0)
            try:
                val = float(val)
            except Exception:
                val = 0.0
            display_val = round(val, 1)
            classes = ["macro-knob"]
            if info.get("parameters"):
                classes.append(f"macro-{i}")
            cls_str = " ".join(classes)
            html.append(
                f'<div class="{cls_str}" data-index="{i}">'
                f'<span class="macro-label{label_class}" data-index="{i}">{name}</span>'
                f'<input id="macro_{i}_dial" type="range" class="macro-dial input-knob" '
                f'data-target="macro_{i}_value" data-display="macro_{i}_disp" '
                f'value="{display_val}" min="0" max="127" step="0.1" data-decimals="1">'
                f'<span id="macro_{i}_disp" class="macro-number"></span>'
                f'<input type="hidden" name="macro_{i}_value" value="{display_val}">' 
                f'</div>'
            )
        html.append('</div>')
        return ''.join(html)
