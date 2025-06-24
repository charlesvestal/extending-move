#!/usr/bin/env python3
import os
import json
import math

from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.fx_chain_handler import (
    extract_fx_parameters,
    save_fx_chain_with_macros,
    update_fx_parameter_values,
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
            "new_preset_name": "",
            "schema_json": "{}",
            "param_count": 0,
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        if action == "reset_preset":
            return self.handle_get()

        preset_path = form.getvalue("preset_select")
        if not preset_path:
            return self.format_error_response("No preset selected")

        try:
            with open(preset_path, "r") as f:
                preset_data = json.load(f)
        except Exception:
            preset_data = {}

        effect_kind = preset_data.get("kind")
        if effect_kind == "audioEffectRack":
            chains = preset_data.get("chains", [])
            if chains and len(chains) == 1:
                devs = chains[0].get("devices", [])
                if devs and len(devs) == 1:
                    effect_kind = devs[0].get("kind")

        message = ""
        if action == "save_chain":
            macros_data_str = form.getvalue("macros_data") or "[]"
            try:
                macros = json.loads(macros_data_str)
            except Exception:
                macros = []
            try:
                pcount = int(form.getvalue("param_count", "0"))
            except ValueError:
                pcount = 0
            param_updates = {}
            for i in range(pcount):
                pname = form.getvalue(f"param_{i}_name")
                pval = form.getvalue(f"param_{i}_value")
                if pname is None or pval is None:
                    continue
                if effect_kind == "channelEq" and pname in {"Gain", "HighShelfGain", "LowShelfGain", "MidGain"}:
                    try:
                        db_val = float(pval)
                        pval = str(10 ** (db_val / 20))
                    except Exception:
                        pass
                param_updates[pname] = pval
            new_name = form.getvalue("new_preset_name")
            if not new_name:
                new_name = os.path.basename(preset_path)
            if not new_name.endswith(".ablpreset") and not new_name.endswith(".json"):
                new_name += ".ablpreset"
            output_path = os.path.join(USER_LIBRARY_DIR, new_name)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result = save_fx_chain_with_macros(preset_path, macros, output_path)
            if not result["success"]:
                return self.format_error_response(result["message"])
            refresh_success, refresh_message = refresh_library()
            message = result["message"]
            if refresh_success:
                message += " Library refreshed."
            else:
                message += f" Library refresh failed: {refresh_message}"
            preset_path = output_path
            if param_updates:
                upd = update_fx_parameter_values(preset_path, param_updates, preset_path)
                if not upd["success"]:
                    return self.format_error_response(upd["message"])
                message += f" {upd['message']}"
        elif action == "select_preset":
            message = f"Selected preset: {os.path.basename(preset_path)}"
        else:
            return self.format_error_response("Unknown action")

        param_info = extract_fx_parameters(preset_path)
        params_html = ""
        available_params_json = "[]"
        param_paths_json = "{}"
        param_count = 0
        schema_json = "{}"
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
            params_html = self.generate_params_html(param_info["parameters"], mapped_info, effect_kind)
            available_params_json = json.dumps([p["name"] for p in param_info["parameters"]])
            param_paths_json = json.dumps(param_info.get("parameter_paths", {}))
            param_count = len(param_info["parameters"])
            if effect_kind in {"channelEq", "chorus", "delay"}:
                from core.fx_browser_handler import load_audio_effects_schema
                schema = load_audio_effects_schema().get(effect_kind, {}).get("parameters", {})
                schema_json = json.dumps(schema)
        else:
            macro_info = extract_macro_information(preset_path)
            macro_knobs_html = self.generate_macro_knobs_html(macro_info.get("macros", []))
            macros_json = json.dumps(macro_info.get("macros", []))

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
            "new_preset_name": os.path.basename(preset_path),
            "schema_json": schema_json,
            "param_count": param_count,
        }

    def build_param_item(self, idx, name, value, meta, mapped):
        """Return HTML for a single parameter control."""
        cls = "param-item"
        if name in mapped:
            cls += f" param-mapped macro-{mapped[name]['macro_index']}"
        html = [f'<div class="{cls}" data-name="{name}">']
        html.append(f'<span class="param-label">{name}</span>')
        p_type = meta.get("type")
        if p_type == "boolean":
            checked = "checked" if str(value).lower() in ("1", "true") else ""
            html.append(
                f'<input type="checkbox" class="param-toggle input-switch" id="param_{idx}_toggle" '
                f'data-target="param_{idx}_value" data-true-value="1" data-false-value="0" {checked}>'
            )
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{int(bool(value))}">')
        elif p_type == "enum":
            opts = meta.get("values", [])
            html.append(f'<select class="param-select" name="param_{idx}_value">')
            for opt in opts:
                sel = " selected" if str(value) == str(opt) else ""
                html.append(f'<option value="{opt}"{sel}>{opt}</option>')
            html.append('</select>')
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
        else:
            attrs = []
            if "min" in meta:
                attrs.append(f'min="{meta["min"]}"')
            if "max" in meta:
                attrs.append(f'max="{meta["max"]}"')
            if "step" in meta:
                attrs.append(f'step="{meta["step"]}"')
            if "unit" in meta:
                attrs.append(f'data-unit="{meta["unit"]}"')
            if "decimals" in meta:
                attrs.append(f'data-decimals="{meta["decimals"]}"')
            if "curve" in meta:
                attrs.append(f'data-curve="{meta["curve"]}"')
            attr_str = " ".join(attrs)
            html.append(
                f'<input id="param_{idx}_dial" type="range" class="param-dial input-knob" '
                f'data-target="param_{idx}_value" data-display="param_{idx}_disp" value="{value}" {attr_str}>'
            )
            html.append(f'<span id="param_{idx}_disp" class="param-number"></span>')
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
        html.append(f'<input type="hidden" name="param_{idx}_name" value="{name}">')
        html.append('</div>')
        return "".join(html)

    def generate_params_html(self, params, mapped, effect_kind=None):
        if effect_kind == "channelEq":
            order = [
                "Enabled",
                "Gain",
                "HighShelfGain",
                "HighpassOn",
                "LowShelfGain",
                "MidFrequency",
                "MidGain",
            ]
            values = {p["name"]: p["value"] for p in params}
            html = ["<div class=\"param-panel\"><div class=\"param-items\">"]
            idx = 0
            for name in order:
                if name not in values:
                    continue
                val = values[name]
                cls = "param-item"
                if name in mapped:
                    cls += f" param-mapped macro-{mapped[name]['macro_index']}"
                html.append(f'<div class="{cls}" data-name="{name}">')
                html.append(f'<span class="param-label">{name}</span>')
                if name in {"Enabled", "HighpassOn"}:
                    checked = "checked" if str(val).lower() in ("1", "true") else ""
                    html.append(
                        f'<input type="checkbox" class="param-toggle input-switch" id="param_{idx}_toggle" '
                        f'data-target="param_{idx}_value" data-true-value="1" data-false-value="0" {checked}>'
                    )
                    html.append(f'<input type="hidden" name="param_{idx}_value" value="{int(bool(val))}">')
                elif name == "MidFrequency":
                    html.append(
                        f'<input id="param_{idx}_dial" type="range" class="param-dial input-knob" '
                        f'data-target="param_{idx}_value" data-display="param_{idx}_disp" value="{val}" '
                        f'min="120" max="750000" step="1" data-unit="Hz" data-decimals="0">'
                    )
                    html.append(f'<span id="param_{idx}_disp" class="param-number"></span>')
                    html.append(f'<input type="hidden" name="param_{idx}_value" value="{val}">')
                else:
                    db = 0.0
                    try:
                        db = 20 * math.log10(float(val))
                    except Exception:
                        pass
                    html.append(
                        f'<input id="param_{idx}_dial" type="range" class="param-dial input-knob" '
                        f'data-target="param_{idx}_value" data-display="param_{idx}_disp" value="{db:.1f}" '
                        f'min="-15" max="15" step="0.1" data-unit="dB" data-decimals="1">'
                    )
                    html.append(f'<span id="param_{idx}_disp" class="param-number"></span>')
                    html.append(f'<input type="hidden" name="param_{idx}_value" value="{db:.1f}">')
                html.append(f'<input type="hidden" name="param_{idx}_name" value="{name}">')
                html.append('</div>')
                idx += 1
            html.append('</div></div>')
            return "".join(html)

        if effect_kind in {"chorus", "delay"}:
            from core.fx_browser_handler import load_audio_effects_schema
            schema = load_audio_effects_schema().get(effect_kind, {}).get("parameters", {})
            if effect_kind == "chorus":
                order = [
                    "Enabled",
                    "Amount",
                    "DryWet",
                    "Feedback",
                    "HighpassEnabled",
                    "HighpassFrequency",
                    "InvertFeedback",
                    "Mode",
                    "OutputGain",
                    "Rate",
                    "Shaping",
                    "VibratoOffset",
                    "Warmth",
                    "Width",
                ]
            else:
                order = [
                    "DelayLine_CompatibilityMode",
                    "DelayLine_Link",
                    "DelayLine_OffsetL",
                    "DelayLine_OffsetR",
                    "DelayLine_PingPong",
                    "DelayLine_PingPongDelayTimeL",
                    "DelayLine_PingPongDelayTimeR",
                    "DelayLine_SimpleDelayTimeL",
                    "DelayLine_SimpleDelayTimeR",
                    "DelayLine_SmoothingMode",
                    "DelayLine_SyncL",
                    "DelayLine_SyncR",
                    "DelayLine_SyncedSixteenthL",
                    "DelayLine_SyncedSixteenthR",
                    "DelayLine_TimeL",
                    "DelayLine_TimeR",
                    "DryWet",
                    "DryWetMode",
                    "EcoProcessing",
                    "Enabled",
                    "Feedback",
                    "Filter_Bandwidth",
                    "Filter_Frequency",
                    "Filter_On",
                    "Freeze",
                    "Modulation_AmountFilter",
                    "Modulation_AmountTime",
                    "Modulation_Frequency",
                ]
            values = {p["name"]: p["value"] for p in params}
            html = ["<div class=\"param-panel\"><div class=\"param-items\">"]
            idx = 0
            for name in order:
                if name not in values:
                    continue
                meta = schema.get(name, {})
                html.append(self.build_param_item(idx, name, values[name], meta, mapped))
                idx += 1
            html.append('</div></div>')
            return ''.join(html)

        html = []
        for p in params:
            name = p.get("name")
            value = p.get("value")
            cls = "param-item"
            if name in mapped:
                cls += f" param-mapped macro-{mapped[name]['macro_index']}"
            html.append(f'<div class="{cls}" data-name="{name}">{name}: {value}</div>')
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
