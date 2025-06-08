#!/usr/bin/env python3
import os
import json
import logging

from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.synth_preset_inspector_handler import (
    extract_parameter_values,
    load_drift_schema,
    extract_macro_information,
)
from core.synth_param_editor_handler import (
    update_parameter_values,
    update_macro_values,
)
from core.refresh_handler import refresh_library

# Path to the preset used when creating a new preset. Prefer the version in the
# user's library but fall back to the bundled example if it doesn't exist.
DEFAULT_PRESET = os.path.join(
    "/data/UserData/UserLibrary/Track Presets",
    "Drift",
    "Analog Shape - Core.json",
)
if not os.path.exists(DEFAULT_PRESET):
    DEFAULT_PRESET = os.path.join(
        "examples",
        "Track Presets",
        "Drift",
        "Analog Shape - Core.json",
    )

logger = logging.getLogger(__name__)

# Colors used to highlight macro-controlled parameters
MACRO_HIGHLIGHT_COLORS = {
    0: "#191970",  # midnightblue
    1: "#006400",  # darkgreen
    2: "#ff0000",  # red
    3: "#ffd700",  # gold
    4: "#00ff00",  # lime
    5: "#00ffff",  # aqua
    6: "#ff00ff",  # fuchsia
    7: "#ffb6c1",  # lightpink
}


class SynthParamEditorHandler(BaseHandler):
    def handle_get(self):
        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/synth-params',
            'preset_select',
            'select_preset',
            filter_key='drift',
        )
        schema = load_drift_schema()
        return {
            'message': 'Select a Drift preset from the list or create a new one',
            'message_type': 'info',
            'file_browser_html': browser_html,
            'params_html': '',
            'selected_preset': None,
            'param_count': 0,
            'browser_root': base_dir,
            'browser_filter': 'drift',
            'schema_json': json.dumps(schema),
            'default_preset_path': DEFAULT_PRESET,
            'macro_knobs_html': '',
            'rename_checked': False,
        }

    def handle_post(self, form):
        action = form.getvalue('action')
        if action == 'reset_preset':
            return self.handle_get()

        if action == 'new_preset':
            preset_path = DEFAULT_PRESET
        else:
            preset_path = form.getvalue('preset_select')

        if not preset_path:
            return self.format_error_response("No preset selected")

        message = ''
        rename_flag = False
        if action == 'save_params':
            try:
                count = int(form.getvalue('param_count', '0'))
            except ValueError:
                count = 0
            updates = {}
            for i in range(count):
                name = form.getvalue(f'param_{i}_name')
                value = form.getvalue(f'param_{i}_value')
                if name is not None and value is not None:
                    updates[name] = value
            rename_flag = form.getvalue('rename') in ('on', 'true', '1')
            new_name = form.getvalue('new_preset_name')
            output_path = None
            if rename_flag and new_name:
                directory = os.path.dirname(preset_path)
                if not new_name.endswith('.ablpreset'):
                    new_name += '.ablpreset'
                output_path = os.path.join(directory, new_name)
            result = update_parameter_values(preset_path, updates, output_path)
            if not result['success']:
                return self.format_error_response(result['message'])
            preset_path = result['path']

            macro_updates = {}
            for i in range(8):
                val = form.getvalue(f'macro_{i}_value')
                if val is not None:
                    macro_updates[i] = val
            macro_result = update_macro_values(preset_path, macro_updates, preset_path)
            if not macro_result['success']:
                return self.format_error_response(macro_result['message'])

            message = result['message'] + "; " + macro_result['message']
            if output_path:
                message += f" Saved as {os.path.basename(output_path)}"
            refresh_success, refresh_message = refresh_library()
            if refresh_success:
                message += " Library refreshed."
            else:
                message += f" Library refresh failed: {refresh_message}"
        elif action in ['select_preset', 'new_preset']:
            if action == 'new_preset':
                message = "Loaded default preset"
            else:
                message = f"Selected preset: {os.path.basename(preset_path)}"
        else:
            return self.format_error_response("Unknown action")

        values = extract_parameter_values(preset_path)
        params_html = ''
        param_count = 0

        macro_knobs_html = ''
        macro_info = extract_macro_information(preset_path)
        mapped_params = {}
        if macro_info['success']:
            macro_knobs_html = self.generate_macro_knobs_html(macro_info['macros'])
            mapped_params = macro_info.get('mapped_parameters', {})

        if values['success']:
            params_html = self.generate_params_html(values['parameters'], mapped_params)
            param_count = len(values['parameters'])

        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/synth-params',
            'preset_select',
            'select_preset',
            filter_key='drift',
        )
        return {
            'message': message,
            'message_type': 'success',
            'file_browser_html': browser_html,
            'params_html': params_html,
            'selected_preset': preset_path,
            'param_count': param_count,
            'browser_root': base_dir,
            'browser_filter': 'drift',
            'schema_json': json.dumps(load_drift_schema()),
            'default_preset_path': DEFAULT_PRESET,
            'macro_knobs_html': macro_knobs_html,
            'rename_checked': rename_flag if action == 'save_params' else False,
        }

    SECTION_ORDER = [
        "Oscillators",
        "Mixer",
        "Filter",
        "Envelopes",
        "LFO",
        "Modulation",
        "Global",
        "Extras",
        "Other",
    ]

    LABEL_OVERRIDES = {
        # Oscillators
        "Oscillator1_Type": "Osc 1",
        "Oscillator1_Transpose": "Oct",
        "Oscillator1_Shape": "Shape",
        "Oscillator1_ShapeModSource": "Shape Mod Source",
        "Oscillator1_ShapeMod": "Shape Mod Amount",
        "Oscillator2_Type": "Osc 2",
        "Oscillator2_Transpose": "Oct",
        "Oscillator2_Detune": "Detune",
        "PitchModulation_Source1": "Source",
        "PitchModulation_Amount1": "Amount",
        "PitchModulation_Source2": "Source",
        "PitchModulation_Amount2": "Amount",

        # Mixer
        "Mixer_OscillatorOn1": "On/Off",
        "Mixer_OscillatorGain1": "Osc 1",
        "Filter_OscillatorThrough1": "Filter",
        "Mixer_OscillatorOn2": "On/Off",
        "Mixer_OscillatorGain2": "Osc 2",
        "Filter_OscillatorThrough2": "Filter",
        "Mixer_NoiseOn": "On/Off",
        "Mixer_NoiseLevel": "Noise",
        "Filter_NoiseThrough": "Filter",

        # Filter
        "Filter_Frequency": "Freq",
        "Filter_Type": "Type",
        "Filter_Tracking": "Key",
        "Filter_Resonance": "Res",
        "Filter_HiPassFrequency": "HP",
        "Filter_ModSource1": "Mod Source 1",
        "Filter_ModAmount1": "Mod Amount 1",
        "Filter_ModSource2": "Mod Source 2",
        "Filter_ModAmount2": "Mod Amount 2",

        # Envelopes
        "Envelope1_Attack": "Attack",
        "Envelope1_Decay": "Decay",
        "Envelope1_Sustain": "Sustain",
        "Envelope1_Release": "Release",
        "Envelope2_Attack": "Attack",
        "Envelope2_Decay": "Decay",
        "Envelope2_Sustain": "Sustain",
        "Envelope2_Release": "Release",
        "CyclingEnvelope_MidPoint": "Tilt",
        "CyclingEnvelope_Hold": "Hold",
        "CyclingEnvelope_Rate": "Rate",
        "CyclingEnvelope_Ratio": "1:1",
        "CyclingEnvelope_Time": "ms",
        "CyclingEnvelope_SyncedRate": "Sync",
        "CyclingEnvelope_Mode": "Mode",

        # LFO
        "Lfo_Shape": "Shape",
        "Lfo_Rate": "Rate",
        "Lfo_Time": "Rate",
        "Lfo_Ratio": "Rate",
        "Lfo_SyncedRate": "Rate",
        "Lfo_Retrigger": "R",
        "Lfo_Amount": "Amount",
        "Lfo_ModSource": "Mod Source",
        "Lfo_ModAmount": "Mod Amount",

        # Modulation Matrix
        "ModulationMatrix_Source1": "Source",
        "ModulationMatrix_Target1": "Destination",
        "ModulationMatrix_Amount1": "Amount",
        "ModulationMatrix_Source2": "Source",
        "ModulationMatrix_Target2": "Destination",
        "ModulationMatrix_Amount2": "Amount",
        "ModulationMatrix_Source3": "Source",
        "ModulationMatrix_Target3": "Destination",
        "ModulationMatrix_Amount3": "Amount",

        # Global
        "Global_VoiceMode": "Mode",
        "Global_VoiceCount": "Voices",
        "Global_MonoVoiceDepth": "Mono Thickness",
        "Global_StereoVoiceDepth": "Stereo Spread",
        "Global_UnisonVoiceDepth": "Unison Strength",
        "Global_PolyVoiceDepth": "Poly Depth",
        "Global_Legato": "Legato",
        "Global_Glide": "Glide",
        "Global_DriftDepth": "Drift",
        "Global_Volume": "Volume",
        "Global_Envelope2Mode": "Env/Cyc",
        "Global_VolVelMod": "Vel > Vol",
        "Global_Transpose": "Transpose",
        "Global_NotePitchBend": "Note PB",
        "Global_PitchBendRange": "PB Range",
        "Global_ResetOscillatorPhase": "R",
    }

    # Short labels for oscillator waveforms
    OSC_WAVE_SHORT = {
        "Pulse": "Pulse",
        "Rectangle": "Rect",
        "Saturated": "Sat",
        "Saw": "Saw",
        "Shark Tooth": "Shark",
        "Sine": "Sine",
        "Triangle": "Tri",
    }

    # Short labels for LFO shapes
    LFO_WAVE_SHORT = {
        "Exponential Env": "Exp Env",
        "Sample & Hold": "S+H",
        "Saw Down": "Saw Dn",
        "Saw Up": "Saw Up",
        "Sine": "Sine",
        "Square": "Square",
        "Triangle": "Tri",
        "Wander": "Wndr",
    }

    # Parameters that should display without a text label
    UNLABELED_PARAMS = {
        "Oscillator1_ShapeModSource",
        "Oscillator1_ShapeMod",
        "PitchModulation_Source1",
        "PitchModulation_Source2",
        "PitchModulation_Amount1",
        "PitchModulation_Amount2",
        "Filter_ModSource1",
        "Filter_ModSource2",
        "Filter_ModAmount1",
        "Filter_ModAmount2",
        "Global_Envelope2Mode",
        "ModulationMatrix_Source1",
        "ModulationMatrix_Amount1",
        "ModulationMatrix_Target1",
        "ModulationMatrix_Source2",
        "ModulationMatrix_Amount2",
        "ModulationMatrix_Target2",
        "ModulationMatrix_Source3",
        "ModulationMatrix_Amount3",
        "ModulationMatrix_Target3",
    }

    # Parameters that use a horizontal slider instead of a dial
    SLIDER_PARAMS = {
        "Oscillator1_ShapeMod",
        "PitchModulation_Amount1",
        "PitchModulation_Amount2",
        "Filter_ModAmount1",
        "Filter_ModAmount2",
        "Global_DriftDepth",
        "Global_Glide",
        "Global_VolVelMod",
        "Global_Transpose",
        "Global_PitchBendRange",
        "ModulationMatrix_Amount1",
        "ModulationMatrix_Amount2",
        "ModulationMatrix_Amount3",
        "Lfo_ModAmount",
        "Filter_Tracking",

    }

    def _build_param_item(self, idx, name, value, meta, label=None,
                           hide_label=False, slider=False, extra_classes=""):
        """Create HTML for a single parameter control."""
        p_type = meta.get("type")
        label = label if label is not None else self.LABEL_OVERRIDES.get(name, name)

        classes = "param-item"
        if extra_classes:
            classes += f" {extra_classes}"
        html = [f'<div class="{classes}" data-name="{name}">']
        if not hide_label:
            html.append(f'<span class="param-label">{label}</span>')

        if name == "Global_Envelope2Mode":
            true_val = "Cyc"
            false_val = "Env"
            checked = "checked" if value == true_val else ""
            html.append(
                f'<input type="checkbox" id="param_{idx}_toggle" class="param-toggle input-switch" '
                f'data-target="param_{idx}_value" data-true-value="{true_val}" data-false-value="{false_val}" {checked}>'
            )
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
        elif p_type == "enum" and meta.get("options"):
            select_class = "param-select"
            if name == "Filter_Type":
                select_class += " filter-type-select"
            html.append(f'<select class="{select_class}" name="param_{idx}_value">')
            short_map = {}
            if name in ("Oscillator1_Type", "Oscillator2_Type"):
                short_map = self.OSC_WAVE_SHORT
            elif name == "Lfo_Shape":
                short_map = self.LFO_WAVE_SHORT
            for opt in meta["options"]:
                sel = " selected" if str(value) == str(opt) else ""
                label_opt = short_map.get(opt, opt)
                title_attr = f' title="{opt}"' if label_opt != opt else ""
                html.append(f'<option value="{opt}"{title_attr}{sel}>{label_opt}</option>')
            html.append('</select>')
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
        elif p_type == "boolean":
            bool_val = 1 if str(value).lower() in ("true", "1") else 0
            html.append(
                f'<input type="checkbox" id="param_{idx}_toggle" class="param-toggle input-switch" '
                f'data-target="param_{idx}_value" data-true-value="1" data-false-value="0"'
                f' {"checked" if bool_val else ""}>'
            )
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{bool_val}">')
        elif name == "Global_SerialNumber":
            min_attr = f' min="{meta.get("min")}"' if meta.get("min") is not None else ''
            max_attr = f' max="{meta.get("max")}"' if meta.get("max") is not None else ''
            html.append(
                f'<input type="number" class="param-input" name="param_{idx}_value" value="{value}"{min_attr}{max_attr}>'
            )
        else:
            min_val = meta.get("min")
            max_val = meta.get("max")
            decimals = meta.get("decimals")
            step_val = meta.get("step")
            if decimals is not None and step_val is None:
                step_val = 10 ** (-decimals)
            if step_val is None and min_val is not None and max_val is not None and max_val <= 1 and min_val >= -1:
                step_val = 0.01
            unit_val = meta.get("unit")
            if slider:
                classes = ["rect-slider"]
                if min_val is not None and max_val is not None and min_val < 0 < max_val:
                    classes.append("center")
                attrs = []
                if min_val is not None:
                    attrs.append(f'data-min="{min_val}"')
                if max_val is not None:
                    attrs.append(f'data-max="{max_val}"')
                if step_val is not None:
                    attrs.append(f'data-step="{step_val}"')
                if decimals is not None:
                    attrs.append(f'data-decimals="{decimals}"')
                if unit_val:
                    attrs.append(f'data-unit="{unit_val}"')
                attrs.append(f'data-target="param_{idx}_value"')
                attrs.append(f'data-value="{value}"')
                attr_str = " ".join(attrs)
                html.append(
                    f'<div id="param_{idx}_slider" class="{" ".join(classes)}" {attr_str}></div>'
                )
                html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
            else:
                min_attr = f' min="{min_val}"' if min_val is not None else ''
                max_attr = f' max="{max_val}"' if max_val is not None else ''
                step_attr = f' step="{step_val}"' if step_val is not None else ''
                unit_attr = f' data-unit="{unit_val}"' if unit_val else ''
                disp_id = f'param_{idx}_display'
                html.append(
                    f'<input id="param_{idx}_dial" type="range" class="param-dial input-knob" data-target="param_{idx}_value" '
                    f'data-display="{disp_id}" value="{value}"{min_attr}{max_attr}{step_attr}{unit_attr}>'
                )
                html.append(f'<span id="{disp_id}" class="param-number"></span>')
                html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')

        html.append(f'<input type="hidden" name="param_{idx}_name" value="{name}">')
        html.append('</div>')
        return ''.join(html)

    def _get_section(self, name):
        if name == "Global_Envelope2Mode":
            return "Envelopes"
        if name.startswith(("Oscillator1_", "Oscillator2_", "PitchModulation_")):
            return "Oscillators"
        if name.startswith("Mixer_") or name.startswith("Filter_OscillatorThrough") or name.startswith("Filter_NoiseThrough"):
            return "Mixer"
        if name.startswith("Filter_"):
            return "Filter"
        if name.startswith(("Envelope1_", "Envelope2_", "CyclingEnvelope_")):
            return "Envelopes"
        if name.startswith("Lfo_"):
            return "LFO"
        if name.startswith("ModulationMatrix_"):
            return "Modulation"
        if name.startswith("Global_"):
            if name in {
                "Global_HiQuality",
                "Global_MonoVoiceDepth",
                "Global_PolyVoiceDepth",
                "Global_ResetOscillatorPhase",
                "Global_StereoVoiceDepth",
                "Global_UnisonVoiceDepth",
                "Global_SerialNumber",
            }:
                return "Extras"
            return "Global"
        return "Other"

    def generate_params_html(self, params, mapped_parameters=None):
        """Return HTML controls for the given parameter values."""
        if not params:
            return '<p>No parameters found.</p>'

        if mapped_parameters is None:
            mapped_parameters = {}

        schema = load_drift_schema()
        sections = {s: [] for s in self.SECTION_ORDER}
        filter_items: dict[str, str] = {}
        osc_items: dict[str, str] = {}
        env_items: dict[str, str] = {}
        lfo_items: dict[str, str] = {}
        mixer_items: dict[str, str] = {}
        global_items: dict[str, str] = {}
        extras_items: dict[str, str] = {}
        mod_items: dict[str, str] = {}
        cycling_mode_val = None
        lfo_mode_val = None

        for i, item in enumerate(params):
            name = item['name']
            val = item['value']
            meta = dict(schema.get(name, {}))

            if name in ("Oscillator1_Transpose", "Oscillator2_Transpose") and meta.get("unit") == "st":
                meta.pop("unit", None)

            hide = name in self.UNLABELED_PARAMS
            slider = name in self.SLIDER_PARAMS

            extra = ""
            if name == "CyclingEnvelope_Rate":
                extra = "cycle-rate freq-rate"
            elif name == "CyclingEnvelope_Ratio":
                extra = "cycle-rate ratio-rate"
            elif name == "CyclingEnvelope_Time":
                extra = "cycle-rate time-rate"
            elif name == "CyclingEnvelope_SyncedRate":
                extra = "cycle-rate sync-rate"
            elif name == "Lfo_Rate":
                extra = "lfo-rate freq-rate"
            elif name == "Lfo_Ratio":
                extra = "lfo-rate ratio-rate"
            elif name == "Lfo_Time":
                extra = "lfo-rate time-rate"
            elif name == "Lfo_SyncedRate":
                extra = "lfo-rate sync-rate"

            if name in mapped_parameters:
                macro_idx = mapped_parameters[name]['macro_index']
                extra = f"{extra} macro-{macro_idx}".strip()

            html = self._build_param_item(
                i,
                name,
                val,
                meta,
                label=self.LABEL_OVERRIDES.get(name, name),
                hide_label=hide,
                slider=slider,
                extra_classes=extra,
            )

            if name == "CyclingEnvelope_Mode":
                cycling_mode_val = val
            if name == "Lfo_Mode":
                lfo_mode_val = val

            section = self._get_section(name)
            if section == "Filter":
                filter_items[name] = html
            elif section == "Oscillators":
                osc_items[name] = html
            elif section == "Envelopes":
                env_items[name] = html
            elif section == "LFO":
                lfo_items[name] = html
            elif section == "Mixer":
                mixer_items[name] = html
            elif section == "Global":
                global_items[name] = html
            elif section == "Extras":
                extras_items[name] = html
            elif section == "Modulation":
                mod_items[name] = html
            else:
                sections[section].append(html)

        if filter_items:
            filter_rows = [
                ["Filter_Frequency", "Filter_Type"],
                ["Filter_Tracking"],
                ["Filter_Resonance", "Filter_HiPassFrequency"],
            ]
            ordered = []
            for row in filter_rows:
                row_html = "".join(filter_items.pop(p, "") for p in row if p in filter_items)
                if row_html:
                    ordered.append(f'<div class="param-row">{row_html}</div>')

            src1 = filter_items.pop("Filter_ModSource1", "")
            amt1 = filter_items.pop("Filter_ModAmount1", "")
            src2 = filter_items.pop("Filter_ModSource2", "")
            amt2 = filter_items.pop("Filter_ModAmount2", "")
            pair1 = f'<div class="param-pair">{src1}{amt1}</div>' if (src1 or amt1) else ""
            pair2 = f'<div class="param-pair">{src2}{amt2}</div>' if (src2 or amt2) else ""
            if pair1.strip() or pair2.strip():
                ordered.append('<div class="freq-mod-label">Freq Mod</div>')
                ordered.append(f'<div class="param-row filter-mod-row">{pair1}{pair2}</div>')

            ordered.extend(filter_items.values())
            sections["Filter"] = ordered

        if mixer_items:
            mixer_rows = [
                ["Mixer_OscillatorOn1", "Mixer_OscillatorGain1", "Filter_OscillatorThrough1"],
                ["Mixer_OscillatorOn2", "Mixer_OscillatorGain2", "Filter_OscillatorThrough2"],
                ["Mixer_NoiseOn", "Mixer_NoiseLevel", "Filter_NoiseThrough"],
            ]
            ordered = []
            for row in mixer_rows:
                row_html = "".join(mixer_items.pop(p, "") for p in row if p in mixer_items)
                if row_html:
                    ordered.append(f'<div class="param-row">{row_html}</div>')
            ordered.extend(mixer_items.values())
            sections["Mixer"] = ordered

        if osc_items:
            ordered = []
            row1_parts = [
                osc_items.pop("Oscillator1_Type", ""),
                osc_items.pop("Oscillator1_Transpose", ""),
                osc_items.pop("Oscillator1_Shape", ""),
            ]
            shape_src = osc_items.pop("Oscillator1_ShapeModSource", "")
            shape_amt = osc_items.pop("Oscillator1_ShapeMod", "")
            shape_pair = f'<div class="param-pair">{shape_src}{shape_amt}</div>' if (shape_src or shape_amt) else ""
            row1 = "".join(row1_parts) + shape_pair
            if row1:
                ordered.append(f'<div class="param-row">{row1}</div>')

            row2 = "".join([
                osc_items.pop("Oscillator2_Type", ""),
                osc_items.pop("Oscillator2_Transpose", ""),
                osc_items.pop("Oscillator2_Detune", ""),
            ])
            if row2:
                ordered.append(f'<div class="param-row">{row2}</div>')

            pm_pair1 = (
                f'<div class="param-pair">{osc_items.pop("PitchModulation_Source1", "")}'
                f'{osc_items.pop("PitchModulation_Amount1", "")}</div>'
            )
            pm_pair2 = (
                f'<div class="param-pair">{osc_items.pop("PitchModulation_Source2", "")}'
                f'{osc_items.pop("PitchModulation_Amount2", "")}</div>'
            )
            if pm_pair1.strip() or pm_pair2.strip():
                ordered.append('<div class="pitch-mod-label">Pitch Mod</div>')
                ordered.append(f'<div class="param-row pitch-mod-row">{pm_pair1}{pm_pair2}</div>')

            ordered.extend(osc_items.values())
            sections["Oscillators"] = ordered

        if env_items:
            amp_adsr = [
                env_items.pop("Envelope1_Attack", ""),
                env_items.pop("Envelope1_Decay", ""),
                env_items.pop("Envelope1_Sustain", ""),
                env_items.pop("Envelope1_Release", ""),
            ]
            env2_adsr = [
                env_items.pop("Envelope2_Attack", ""),
                env_items.pop("Envelope2_Decay", ""),
                env_items.pop("Envelope2_Sustain", ""),
                env_items.pop("Envelope2_Release", ""),
            ]
            cycle_toggle = env_items.pop("Global_Envelope2Mode", "")
            cycle_mid = env_items.pop("CyclingEnvelope_MidPoint", "")
            cycle_hold = env_items.pop("CyclingEnvelope_Hold", "")
            cycle_rate = env_items.pop("CyclingEnvelope_Rate", "")
            cycle_ratio = env_items.pop("CyclingEnvelope_Ratio", "")
            cycle_time = env_items.pop("CyclingEnvelope_Time", "")
            cycle_sync = env_items.pop("CyclingEnvelope_SyncedRate", "")
            cycle_mode = env_items.pop("CyclingEnvelope_Mode", "")

            ordered = []
            row1 = "".join(amp_adsr)
            if row1:
                ordered.append(
                    f'<div class="param-row"><span class="param-row-label">Amp envelope</span>{row1}</div>'
                )
            if cycle_toggle:
                ordered.append(
                    f'<div class="param-row env2-mode"><span class="param-row-label">Env/Cyc</span>{cycle_toggle}</div>'
                )
            row2_main = "".join(env2_adsr)
            if row2_main.strip():
                ordered.append(
                    f'<div class="param-row env2-adsr"><span class="param-row-label">Env 2</span>{row2_main}</div>'
                )
            if any([cycle_mid, cycle_hold, cycle_rate, cycle_ratio, cycle_time, cycle_sync, cycle_mode]):
                # Hide unselected rate controls based on current mode
                if cycling_mode_val != "Freq" and cycle_rate:
                    cycle_rate = cycle_rate.replace('param-item"', 'param-item hidden"', 1)
                if cycling_mode_val != "Ratio" and cycle_ratio:
                    cycle_ratio = cycle_ratio.replace('param-item"', 'param-item hidden"', 1)
                if cycling_mode_val != "Time" and cycle_time:
                    cycle_time = cycle_time.replace('param-item"', 'param-item hidden"', 1)
                if cycling_mode_val != "Sync" and cycle_sync:
                    cycle_sync = cycle_sync.replace('param-item"', 'param-item hidden"', 1)

                row3_extra = "".join([
                    cycle_mid,
                    cycle_hold,
                    cycle_rate,
                    cycle_ratio,
                    cycle_time,
                    cycle_sync,
                    cycle_mode,
                ])
                ordered.append(
                    f'<div class="param-row env2-cycling hidden"><span class="param-row-label">Env 2</span>{row3_extra}</div>'
                )

            ordered.extend(env_items.values())
            sections["Envelopes"] = ordered

        if global_items:
            col1_order = [
                "Global_VoiceMode",
                "Global_VoiceCount",
                "Global_DriftDepth",
                "Global_Legato",
                "Global_Glide",
            ]
            col2_order = [
                "Global_Volume",
                "Global_VolVelMod",
                "Global_Transpose",
                "Global_NotePitchBend",
                "Global_PitchBendRange",
            ]
            col1_html = "".join(global_items.pop(n, "") for n in col1_order)
            col2_html = "".join(global_items.pop(n, "") for n in col2_order)
            ordered = []
            if col1_html or col2_html:
                ordered.append(
                    f'<div class="param-columns"><div class="param-column">{col1_html}</div><div class="param-column">{col2_html}</div></div>'
                )
            ordered.extend(global_items.values())
            sections["Global"] = ordered

        if extras_items:
            sections["Extras"] = list(extras_items.values())

        if mod_items:
            mods = []
            for idx in range(1, 4):
                src = mod_items.pop(f"ModulationMatrix_Source{idx}", "")
                amt = mod_items.pop(f"ModulationMatrix_Amount{idx}", "")
                dst = mod_items.pop(f"ModulationMatrix_Target{idx}", "")
                if src or amt or dst:
                    mods.append(
                        f'<div class="param-pair mod-group">'
                        f'<span class="mod-label">Mod {idx}</span>'
                        f'{src}{amt}{dst}'
                        f'</div>'
                    )

            ordered = []
            if mods:
                top = ''.join(mods[:2])
                if top:
                    ordered.append(
                        f'<div class="param-row mod-matrix-row">{top}</div>'
                    )
                if len(mods) >= 3:
                    ordered.append(
                        f'<div class="param-row mod-matrix-row">{mods[2]}</div>'
                    )

            ordered.extend(mod_items.values())
            sections["Modulation"] = ordered

        if lfo_items:
            rate = lfo_items.pop("Lfo_Rate", "")
            ratio = lfo_items.pop("Lfo_Ratio", "")
            time = lfo_items.pop("Lfo_Time", "")
            sync = lfo_items.pop("Lfo_SyncedRate", "")
            mode = lfo_items.pop("Lfo_Mode", "")
            shape = lfo_items.pop("Lfo_Shape", "")
            retrig = lfo_items.pop("Lfo_Retrigger", "")
            amount = lfo_items.pop("Lfo_Amount", "")
            mod_src = lfo_items.pop("Lfo_ModSource", "")
            mod_amt = lfo_items.pop("Lfo_ModAmount", "")

            if lfo_mode_val != "Freq" and rate:
                rate = rate.replace('param-item"', 'param-item hidden"', 1)
            if lfo_mode_val != "Ratio" and ratio:
                ratio = ratio.replace('param-item"', 'param-item hidden"', 1)
            if lfo_mode_val != "Time" and time:
                time = time.replace('param-item"', 'param-item hidden"', 1)
            if lfo_mode_val != "Sync" and sync:
                sync = sync.replace('param-item"', 'param-item hidden"', 1)

            ordered = []
            row1 = "".join([rate, ratio, time, sync, mode])
            if row1.strip():
                ordered.append(f'<div class="param-row lfo-rate-row">{row1}</div>')
            row2 = "".join([shape, retrig])
            if row2.strip():
                ordered.append(f'<div class="param-row">{row2}</div>')
            pair = f'<div class="param-pair">{mod_src}{mod_amt}</div>' if (mod_src or mod_amt) else ""
            row3 = "".join([amount, pair])
            if row3.strip():
                ordered.append(f'<div class="param-row">{row3}</div>')

            ordered.extend(lfo_items.values())
            sections["LFO"] = ordered

        out_html = '<div class="drift-param-panels">'
        bottom_panels = []
        second_row = {"LFO", "Modulation", "Global", "Extras"}
        for sec in self.SECTION_ORDER:
            items = sections.get(sec)
            if not items:
                continue
            cls = sec.lower().replace(' ', '-').replace('+', '')
            panel_html = (
                f'<div class="param-panel {cls}"><h3>{sec}</h3>'
                f'<div class="param-items">{"".join(items)}</div></div>'
            )
            if sec in second_row:
                bottom_panels.append(panel_html)
            else:
                out_html += panel_html
        out_html += '</div>'
        if bottom_panels:
            out_html += '<div class="drift-param-panels">'
            out_html += ''.join(bottom_panels)
            out_html += '</div>'
        return out_html

    def generate_macro_knobs_html(self, macros):
        """Return HTML for a row of macro value knobs."""
        if not macros:
            macros = []

        by_index = {m["index"]: m for m in macros}
        html = ['<div class="macro-knob-row">']
        for i in range(8):
            info = by_index.get(i, {"name": f"Macro {i}", "value": 0.0})
            name = info.get("name", f"Macro {i}")
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
                f'<div class="{cls_str}">' 
                f'<span class="macro-label">{name}</span>'
                f'<input id="macro_{i}_dial" type="range" class="macro-dial input-knob" '
                f'data-target="macro_{i}_value" data-display="macro_{i}_disp" '
                f'value="{display_val}" min="0" max="127" step="0.1" data-decimals="1">'
                f'<span id="macro_{i}_disp" class="macro-number"></span>'
                f'<input type="hidden" name="macro_{i}_value" value="{display_val}">' 
                f'</div>'
            )
        html.append('</div>')
        return ''.join(html)

