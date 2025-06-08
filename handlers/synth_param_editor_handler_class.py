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
        "Global_Envelope2Mode": "Env/Cyc",
        "Global_VolVelMod": "Vel > Vol",
        "Global_Transpose": "Transpose",
        "Global_NotePitchBend": "Note PB",
        "Global_PitchBendRange": "PB Range",
        "Global_ResetOscillatorPhase": "R",
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
    }

    # Parameters that use a horizontal slider instead of a dial
    SLIDER_PARAMS = {
        "Oscillator1_ShapeMod",
        "PitchModulation_Amount1",
        "PitchModulation_Amount2",
        "Filter_ModAmount1",
        "Filter_ModAmount2",
    }

    def _build_param_item(self, idx, name, value, meta, label=None,
                           hide_label=False, slider=False):
        """Create HTML for a single parameter control."""
        p_type = meta.get("type")
        label = label if label is not None else self.LABEL_OVERRIDES.get(name, name)

        html = [f'<div class="param-item" data-name="{name}">']
        if not hide_label:
            html.append(f'<span class="param-label">{label}</span>')

        if p_type == "enum" and meta.get("options"):
            html.append(f'<select name="param_{idx}_value">')
            for opt in meta["options"]:
                sel = " selected" if str(value) == str(opt) else ""
                html.append(f'<option value="{opt}"{sel}>{opt}</option>')
            html.append('</select>')
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
        elif p_type == "boolean":
            bool_val = 1 if str(value).lower() in ("true", "1") else 0
            html.append(
                f'<div id="param_{idx}_toggle" class="param-toggle" '
                f'data-target="param_{idx}_value" data-value="{bool_val}"></div>'
            )
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{bool_val}">')
        else:
            min_attr = f' data-min="{meta.get("min")}"' if meta.get("min") is not None else ''
            max_attr = f' data-max="{meta.get("max")}"' if meta.get("max") is not None else ''
            val_attr = f' data-value="{value}"'
            unit_attr = f' data-unit="{meta.get("unit")}"' if meta.get("unit") else ''
            dec_attr = f' data-decimals="{meta.get("decimals")}"' if meta.get("decimals") is not None else ''
            disp_id = f'param_{idx}_display'
            klass = "param-dial"
            orient = ""
            if slider:
                klass = "param-slider"
                orient = ' data-orientation="horizontal"'
            html.append(
                f'<div id="param_{idx}_dial" class="{klass}" data-target="param_{idx}_value" '
                f'data-display="{disp_id}"{orient}{min_attr}{max_attr}{val_attr}{unit_attr}{dec_attr}></div>'
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
            return "Global"
        return "Other"

    def generate_params_html(self, params):
        """Return HTML controls for the given parameter values."""
        if not params:
            return '<p>No parameters found.</p>'

        schema = load_drift_schema()
        sections = {s: [] for s in self.SECTION_ORDER}
        filter_items: dict[str, str] = {}
        osc_items: dict[str, str] = {}
        env_items: dict[str, str] = {}
        mixer_items: dict[str, str] = {}

        for i, item in enumerate(params):
            name = item['name']
            val = item['value']
            meta = dict(schema.get(name, {}))

            if name in ("Oscillator1_Transpose", "Oscillator2_Transpose") and meta.get("unit") == "st":
                meta.pop("unit", None)

            hide = name in self.UNLABELED_PARAMS
            slider = name in self.SLIDER_PARAMS
            html = self._build_param_item(
                i,
                name,
                val,
                meta,
                label=self.LABEL_OVERRIDES.get(name, name),
                hide_label=hide,
                slider=slider,
            )

            section = self._get_section(name)
            if section == "Filter":
                filter_items[name] = html
            elif section == "Oscillators":
                osc_items[name] = html
            elif section == "Envelopes":
                env_items[name] = html
            elif section == "Mixer":
                mixer_items[name] = html
            else:
                sections[section].append(html)

        if filter_items:
            filter_rows = [
                ["Filter_Frequency", "Filter_Type", "Filter_Tracking"],
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
            cycle_extras = [
                env_items.pop("CyclingEnvelope_MidPoint", ""),
                env_items.pop("CyclingEnvelope_Hold", ""),
                env_items.pop("CyclingEnvelope_Rate", ""),
                env_items.pop("CyclingEnvelope_Mode", ""),
            ]

            ordered = []
            row1 = "".join(amp_adsr)
            if row1:
                ordered.append(
                    f'<div class="param-row"><span class="param-row-label">Amp envelope</span>{row1}</div>'
                )
            row2_main = "".join(env2_adsr) + cycle_toggle
            if row2_main.strip():
                ordered.append(
                    f'<div class="param-row env2-main env2-adsr"><span class="param-row-label">Env 2</span>{row2_main}</div>'
                )
            row3_extra = "".join(cycle_extras)
            if row3_extra.strip():
                ordered.append(
                    f'<div class="param-row env2-cycling hidden"><span class="param-row-label">Env 2</span>{row3_extra}</div>'
                )

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

