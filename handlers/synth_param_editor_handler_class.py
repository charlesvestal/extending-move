#!/usr/bin/env python3
import os
import json
import logging

from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.synth_preset_inspector_handler import (
    extract_parameter_values,
    load_drift_schema,
)
from core.synth_param_editor_handler import update_parameter_values

# Path to the example preset used when creating a new preset
DEFAULT_PRESET = os.path.join(
    "examples",
    "Track Presets",
    "Drift",
    "Analog Shape.ablpreset",
)

logger = logging.getLogger(__name__)


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
            new_name = form.getvalue('new_preset_name')
            output_path = None
            if new_name:
                directory = os.path.dirname(preset_path)
                if not new_name.endswith('.ablpreset'):
                    new_name += '.ablpreset'
                output_path = os.path.join(directory, new_name)
            result = update_parameter_values(preset_path, updates, output_path)
            if not result['success']:
                return self.format_error_response(result['message'])
            message = result['message']
            if output_path:
                message += f" Saved as {os.path.basename(output_path)}"
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
        if values['success']:
            params_html = self.generate_params_html(values['parameters'])
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
        }

    SECTION_ORDER = [
        "Oscillators",
        "Mixer",
        "Filter",
        "Envelopes",
        "LFO",
        "Modulation",
        "Global",
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
        "Mixer_NoiseLevel": "Level",
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
        "CyclingEnvelope_Tilt": "Tilt",
        "CyclingEnvelope_Hold": "Hold",
        "CyclingEnvelope_Rate": "Rate",
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
        "Global_VolVelMod": "Vel > Vol",
        "Global_Transpose": "Transpose",
        "Global_NotePitchBend": "Note PB",
        "Global_PitchBendRange": "PB Range",
        "Global_ResetOscillatorPhase": "R",
    }

    def _get_section(self, name):
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
            return "Global"
        return "Other"

    def generate_params_html(self, params):
        """Return HTML controls for the given parameter values."""
        if not params:
            return '<p>No parameters found.</p>'

        schema = load_drift_schema()
        sections = {s: [] for s in self.SECTION_ORDER}
        filter_items = {}
        osc_items = {}
        env_items = {}
        extra_controls = {}

        def build_control(idx, name, val, meta):
            p_type = meta.get('type')
            if p_type == 'enum' and meta.get('options'):
                ctrl = '<select name="param_%d_value">' % idx
                for opt in meta['options']:
                    selected = ' selected' if str(val) == str(opt) else ''
                    ctrl += f'<option value="{opt}"{selected}>{opt}</option>'
                ctrl += '</select>'
            else:
                min_attr = f' data-min="{meta.get("min")}"' if meta.get("min") is not None else ''
                max_attr = f' data-max="{meta.get("max")}"' if meta.get("max") is not None else ''
                val_attr = f' data-value="{val}"'
                unit_attr = ''
                if meta.get("unit") and meta.get("unit") != 'st':
                    unit_attr = f' data-unit="{meta.get("unit")}"'
                dec_attr = f' data-decimals="{meta.get("decimals")}"' if meta.get("decimals") is not None else ''
                display_id = f'param_{idx}_display'
                slider_names = {
                    "Oscillator1_ShapeMod",
                    "PitchModulation_Amount1",
                    "PitchModulation_Amount2",
                }
                if name in slider_names:
                    ctrl = (
                        f'<div id="param_{idx}_slider" class="param-slider" data-target="param_{idx}_value" '
                        f'data-display="{display_id}"{min_attr}{max_attr}{val_attr}{unit_attr}{dec_attr}></div>'
                    )
                else:
                    ctrl = (
                        f'<div id="param_{idx}_dial" class="param-dial" data-target="param_{idx}_value" '
                        f'data-display="{display_id}"{min_attr}{max_attr}{val_attr}{unit_attr}{dec_attr}></div>'
                    )
                ctrl += f'<span id="{display_id}" class="param-number"></span>'
                ctrl += f'<input type="hidden" name="param_{idx}_value" value="{val}">'
            return ctrl

        def build_item(idx, name, val, meta, hide_label=False):
            label = self.LABEL_OVERRIDES.get(name, name)
            ctrl = build_control(idx, name, val, meta)
            html = '<div class="param-item">'
            if not hide_label:
                html += f'<span class="param-label">{label}</span>'
            html += ctrl
            html += f'<input type="hidden" name="param_{idx}_name" value="{name}"></div>'
            return html, ctrl

        for i, item in enumerate(params):
            name = item['name']
            val = item['value']
            meta = schema.get(name, {})

            hide_label = name in {
                "Oscillator1_ShapeModSource",
                "Oscillator1_ShapeMod",
                "PitchModulation_Source1",
                "PitchModulation_Amount1",
                "PitchModulation_Source2",
                "PitchModulation_Amount2",
            }

            html, ctrl = build_item(i, name, val, meta, hide_label=hide_label)

            if name in {"Oscillator1_ShapeModSource", "Oscillator1_ShapeMod", "PitchModulation_Source1", "PitchModulation_Amount1", "PitchModulation_Source2", "PitchModulation_Amount2"}:
                extra_controls[name] = html  # store full item for later placement
                continue

            section = self._get_section(name)
            if section == "Filter":
                filter_items[name] = html
            elif section == "Oscillators":
                osc_items[name] = html
            elif section == "Envelopes":
                env_items[name] = html
            else:
                sections[section].append(html)

        if filter_items:
            filter_rows = [
                ["Filter_Frequency", "Filter_Type", "Filter_Tracking"],
                ["Filter_Resonance", "Filter_HiPassFrequency"],
                [
                    "Filter_ModSource1",
                    "Filter_ModAmount1",
                    "Filter_ModSource2",
                    "Filter_ModAmount2",
                ],
            ]
            ordered = []
            for row in filter_rows:
                row_html = "".join(filter_items.pop(p, "") for p in row if p in filter_items)
                if row_html:
                    ordered.append(f'<div class="param-row">{row_html}</div>')
            ordered.extend(filter_items.values())
            sections["Filter"] = ordered

        if osc_items:
            ordered = []
            row1 = "".join(osc_items.pop(p, "") for p in [
                "Oscillator1_Type",
                "Oscillator1_Transpose",
                "Oscillator1_Shape",
            ] if p in osc_items)
            shape_src = extra_controls.pop("Oscillator1_ShapeModSource", "")
            shape_amt = extra_controls.pop("Oscillator1_ShapeMod", "")
            if shape_src or shape_amt:
                row1 += f'<div class="shape-mod">{shape_src}{shape_amt}</div>'
            if row1:
                ordered.append(f'<div class="param-row">{row1}</div>')

            row2 = "".join(osc_items.pop(p, "") for p in [
                "Oscillator2_Type",
                "Oscillator2_Transpose",
                "Oscillator2_Detune",
            ] if p in osc_items)
            if row2:
                ordered.append(f'<div class="param-row">{row2}</div>')

            pm_src1 = extra_controls.pop("PitchModulation_Source1", "")
            pm_src2 = extra_controls.pop("PitchModulation_Source2", "")
            pm_amt1 = extra_controls.pop("PitchModulation_Amount1", "")
            pm_amt2 = extra_controls.pop("PitchModulation_Amount2", "")
            pitch_html = ""
            if pm_src1 or pm_src2 or pm_amt1 or pm_amt2:
                pitch_html += '<div class="pitch-mod"><h4>Pitch Mod</h4>'
                row_a = pm_src1 + pm_src2
                row_b = pm_amt1 + pm_amt2
                if row_a:
                    pitch_html += f'<div class="param-row">{row_a}</div>'
                if row_b:
                    pitch_html += f'<div class="param-row">{row_b}</div>'
                pitch_html += '</div>'
            if pitch_html:
                ordered.append(pitch_html)

            ordered.extend(osc_items.values())
            sections["Oscillators"] = ordered

        if env_items:
            env_rows = [
                [
                    "Envelope1_Attack",
                    "Envelope1_Decay",
                    "Envelope1_Sustain",
                    "Envelope1_Release",
                ],
                [
                    "Envelope2_Attack",
                    "Envelope2_Decay",
                    "Envelope2_Sustain",
                    "Envelope2_Release",
                ],
                [
                    "CyclingEnvelope_MidPoint",
                    "CyclingEnvelope_Hold",
                    "CyclingEnvelope_Rate",
                ],
            ]
            ordered = []
            for row in env_rows:
                row_html = "".join(env_items.pop(p, "") for p in row if p in env_items)
                if row_html:
                    ordered.append(f'<div class="param-row">{row_html}</div>')
            ordered.extend(env_items.values())
            sections["Envelopes"] = ordered

        out_html = '<div class="drift-param-panels">'
        for sec in self.SECTION_ORDER:
            items = sections.get(sec)
            if not items:
                continue
            cls = sec.lower().replace(' ', '-').replace('+', '')
            out_html += f'<div class="param-panel {cls}"><h3>{sec}</h3><div class="param-items">'
            out_html += ''.join(items)
            out_html += '</div></div>'
        out_html += '</div>'
        return out_html

