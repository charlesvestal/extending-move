#!/usr/bin/env python3
import os
import json
import logging
import shutil
import re

from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.synth_preset_inspector_handler import (
    extract_parameter_values,
    load_wavetable_schema,
    extract_macro_information,
    update_preset_macro_names,
    update_preset_parameter_mappings,
    delete_parameter_mapping,
    extract_available_parameters,
    load_wavetable_sprites,
    extract_wavetable_sprites,
    update_wavetable_sprites,
    extract_wavetable_mod_matrix,
    update_wavetable_mod_matrix,
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
    "Wavetable",
    "E-Piano Classic.ablpreset",
)
if not os.path.exists(DEFAULT_PRESET):
    DEFAULT_PRESET = os.path.join(
        "examples",
        "Track Presets",
        "Wavetable",
        "E-Piano Classic.ablpreset",
    )

# Directory where new presets are saved
NEW_PRESET_DIR = os.path.join(
    "/data/UserData/UserLibrary/Track Presets",
    "Wavetable",
)

# Base directory for factory presets that should never be modified
# These presets are stored as JSON files under ``/data/CoreLibrary/Track Presets``
# with subfolders for instrument categories (e.g. "Drift").  We only store the
# base path here so that presets in any subfolder are detected correctly.
CORE_LIBRARY_DIR = "/data/CoreLibrary/Track Presets"

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

# Display labels for synced rate values
SYNC_RATE_LABELS = [
    "8", "6", "4", "3", "2", "1.5", "1", "3/4", "1/2", "3/8", "1/3", "5/16",
    "1/4", "3/16", "1/6", "1/8", "1/12", "1/16", "1/24", "1/32", "1/48",
    "1/64",
]

# Parameters that should not be assignable to macros. These cause issues
# with the wavetable editor, so they are removed from the dropdown list
# when editing presets.
EXCLUDED_MACRO_PARAMS = {
    "HiQ",
    "MonoPoly",
    "PolyVoices",
    "Voice_Global_FilterRouting",
    "Voice_Oscillator1_Effects_EffectMode",
    "Voice_Oscillator2_Effects_EffectMode",
    "Voice_Unison_Mode",
    "Voice_Unison_VoiceCount",
}


class WavetableParamEditorHandler(BaseHandler):
    def handle_get(self):
        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/wavetable-params',
            'preset_select',
            'select_preset',
            filter_key='wavetable',
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        schema = load_wavetable_schema()
        sprites = load_wavetable_sprites()
        return {
            'message': 'Select a Wavetable preset from the list or create a new one',
            'message_type': 'info',
            'file_browser_html': browser_html,
            'params_html': '',
            'selected_preset': None,
            'param_count': 0,
            'browser_root': base_dir,
            'browser_filter': 'wavetable',
            'schema_json': json.dumps(schema),
            'default_preset_path': DEFAULT_PRESET,
            'macro_knobs_html': '',
            'rename_checked': False,
            'macros_json': '[]',
            'available_params_json': '[]',
            'param_paths_json': '{}',
            'sprites_json': json.dumps(sprites),
            'sprite1': '',
            'sprite2': '',
            'mod_matrix_json': '[]',
        }

    def handle_post(self, form):
        action = form.getvalue('action')
        if action == 'reset_preset':
            return self.handle_get()

        message = ''
        if action == 'new_preset':
            new_name = form.getvalue('new_preset_name')
            if not new_name:
                return self.format_error_response("Preset name required")
            os.makedirs(NEW_PRESET_DIR, exist_ok=True)
            if not new_name.endswith('.ablpreset') and not new_name.endswith('.json'):
                new_name += '.ablpreset'
            preset_path = os.path.join(NEW_PRESET_DIR, new_name)
            if os.path.exists(preset_path):
                return self.format_error_response("Preset already exists")
            try:
                shutil.copy(DEFAULT_PRESET, preset_path)
                refresh_success, refresh_message = refresh_library()
                if refresh_success:
                    message = (
                        f"Created new preset {os.path.basename(preset_path)}. "
                        "Library refreshed."
                    )
                else:
                    message = (
                        f"Created new preset {os.path.basename(preset_path)}. "
                        f"Library refresh failed: {refresh_message}"
                    )
            except Exception as exc:
                return self.format_error_response(f"Could not create preset: {exc}")
        else:
            preset_path = form.getvalue('preset_select')

        if not preset_path:
            return self.format_error_response("No preset selected")

        is_core = preset_path.startswith(CORE_LIBRARY_DIR)

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
            rename_flag = form.getvalue('rename') in ('on', 'true', '1') or is_core
            new_name = form.getvalue('new_preset_name')
            output_path = None
            if rename_flag:
                if not new_name:
                    new_name = os.path.basename(preset_path)
                # Convert json factory presets to .ablpreset when copying
                if new_name.endswith('.json'):
                    new_name = new_name[:-5]
                if not new_name.endswith('.ablpreset'):
                    new_name += '.ablpreset'
                directory = os.path.dirname(preset_path)
                if is_core:
                    directory = NEW_PRESET_DIR
                output_path = os.path.join(directory, new_name)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result = update_parameter_values(
                preset_path,
                updates,
                output_path,
                device_types=("wavetable",),
            )
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

            macros_data_str = form.getvalue('macros_data')
            if macros_data_str:
                try:
                    macros_data = json.loads(macros_data_str)
                except Exception:
                    macros_data = []
            else:
                macros_data = []

            # Update macro names
            name_updates = {m.get('index'): m.get('name') for m in macros_data}
            name_result = update_preset_macro_names(preset_path, name_updates)
            if not name_result['success']:
                return self.format_error_response(name_result['message'])

            # Determine existing mappings to remove
            existing_info = extract_macro_information(preset_path)
            existing_mapped = existing_info.get('mapped_parameters', {}) if existing_info['success'] else {}

            processed = set()
            for m in macros_data:
                idx = m.get('index')
                for p in m.get('parameters', []):
                    pname = p.get('name')
                    param_updates = {
                        idx: {
                            'parameter': pname,
                            'parameter_path': p.get('path'),
                            'rangeMin': p.get('rangeMin'),
                            'rangeMax': p.get('rangeMax'),
                        }
                    }
                    upd = update_preset_parameter_mappings(preset_path, param_updates)
                    if not upd['success']:
                        return self.format_error_response(upd['message'])
                    processed.add(pname)
                    existing_mapped.pop(pname, None)

            # Remove mappings not present anymore
            for pname, info in existing_mapped.items():
                delete_parameter_mapping(preset_path, info['path'])

            sprite1 = form.getvalue('sprite1')
            sprite2 = form.getvalue('sprite2')
            sprite_res = update_wavetable_sprites(
                preset_path,
                sprite1 if sprite1 is not None else None,
                sprite2 if sprite2 is not None else None,
                preset_path,
            )
            if not sprite_res['success']:
                return self.format_error_response(sprite_res['message'])

            matrix_str = form.getvalue('mod_matrix_data')
            if matrix_str:
                try:
                    matrix_data = json.loads(matrix_str)
                except Exception:
                    matrix_data = []
            else:
                matrix_data = []
            matrix_res = update_wavetable_mod_matrix(preset_path, matrix_data, preset_path)
            if not matrix_res['success']:
                return self.format_error_response(matrix_res['message'])

            message = result['message'] + "; " + macro_result['message']
            if output_path:
                message += f" Saved to {output_path}"
            refresh_success, refresh_message = refresh_library()
            if refresh_success:
                message += " Library refreshed."
            else:
                message += f" Library refresh failed: {refresh_message}"
        elif action in ['select_preset', 'new_preset']:
            if action == 'select_preset':
                if is_core:
                    dest_name = os.path.basename(preset_path)
                    if dest_name.endswith('.json'):
                        dest_name = dest_name[:-5] + '.ablpreset'
                    save_path = os.path.join(NEW_PRESET_DIR, dest_name)
                    message = f"Core Library preset will be saved to {save_path}"
                else:
                    message = f"Selected preset: {os.path.basename(preset_path)}"
        else:
            return self.format_error_response("Unknown action")

        values = extract_parameter_values(preset_path, device_types=("wavetable",))
        params_html = ''
        param_count = 0

        macro_knobs_html = ''
        macro_info = extract_macro_information(preset_path)
        mapped_params = {}
        macros_json = '[]'
        available_params_json = '[]'
        param_paths_json = '{}'
        if macro_info['success']:
            macro_knobs_html = self.generate_macro_knobs_html(macro_info['macros'])
            mapped_params = macro_info.get('mapped_parameters', {})
            macros_for_json = []
            for m in macro_info['macros']:
                mc = dict(m)
                if mc.get('name') == f"Macro {mc.get('index')}":
                    mc['name'] = ""
                macros_for_json.append(mc)
            macros_json = json.dumps(macros_for_json)

        param_info = extract_available_parameters(
            preset_path,
            device_types=("wavetable",),
            schema_loader=load_wavetable_schema,
        )
        if param_info['success']:
            params = [
                p for p in param_info['parameters'] if p not in EXCLUDED_MACRO_PARAMS
            ]
            paths = {
                k: v
                for k, v in param_info.get('parameter_paths', {}).items()
                if k not in EXCLUDED_MACRO_PARAMS
            }
            available_params_json = json.dumps(params)
            param_paths_json = json.dumps(paths)
        
        if values['success']:
            params_html = self.generate_params_html(values['parameters'], mapped_params)
            param_count = len(values['parameters'])

        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/wavetable-params',
            'preset_select',
            'select_preset',
            filter_key='wavetable',
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        sprites_json = json.dumps(load_wavetable_sprites())
        sprite_info = extract_wavetable_sprites(preset_path)
        sprite1 = sprite_info.get('sprite1') if sprite_info.get('success', True) else None
        sprite2 = sprite_info.get('sprite2') if sprite_info.get('success', True) else None
        matrix_info = extract_wavetable_mod_matrix(preset_path)
        mod_matrix_json = json.dumps(matrix_info.get('matrix', [])) if matrix_info.get('success', False) else '[]'
        return {
            'message': message,
            'message_type': 'success',
            'file_browser_html': browser_html,
            'params_html': params_html,
            'selected_preset': preset_path,
            'param_count': param_count,
            'browser_root': base_dir,
            'browser_filter': 'wavetable',
            'schema_json': json.dumps(load_wavetable_schema()),
            'default_preset_path': DEFAULT_PRESET,
            'macro_knobs_html': macro_knobs_html,
            'rename_checked': rename_flag if action == 'save_params' else is_core,
            'macros_json': macros_json,
            'available_params_json': available_params_json,
            'param_paths_json': param_paths_json,
            'sprites_json': sprites_json,
            'mod_matrix_json': mod_matrix_json,
            'sprite1': sprite1 or '',
            'sprite2': sprite2 or '',
        }

    SECTION_ORDER = [
        "Oscillators",
        "FX",
        "Mixer",
        "Filter",
        "Modulation",
        "Global",
        "Envelopes",
        "Extras",
        "Other",
    ]

    SECTION_SUBPANELS = {
        "Oscillators": [
            ("Voice_Oscillator1_", "Oscillator 1", "Oscillator1"),
            ("Voice_Oscillator2_", "Oscillator 2", "Oscillator2"),
            ("Voice_SubOscillator_", "Sub Oscillator", "SubOscillator"),
        ],
        "FX": [
            ("Voice_Oscillator1_Effects_", "Oscillator 1", "Oscillator1_Effects"),
            ("Voice_Oscillator2_Effects_", "Oscillator 2", "Oscillator2_Effects"),
        ],
        "Mixer": [
            ("Voice_Oscillator1_", "Oscillator 1", "Oscillator1"),
            ("Voice_Oscillator2_", "Oscillator 2", "Oscillator2"),
            ("Voice_SubOscillator_", "Sub Oscillator", "SubOscillator"),
        ],
        "Filter": [
            ("Voice_Filter1_", "Voice Filter 1", "Filter"),
            ("Voice_Filter2_", "Voice Filter 2", "Filter"),
        ],
        "Envelopes": [
            ("Voice_Modulators_AmpEnvelope_", "Amp Envelope", "Envelope1"),
            ("Voice_Modulators_Envelope2_", "Envelope 2", "Envelope2"),
            ("Voice_Modulators_Envelope3_", "Envelope 3", "Envelope3"),
        ],
        "Modulation": [
            ("Voice_Modulators_Lfo1_", "LFO 1", "Lfo"),
            ("Voice_Modulators_Lfo2_", "LFO 2", "Lfo"),
        ],
    }

    LABEL_OVERRIDES = {
        # Oscillators
        "Oscillator1_Type": "Osc 1",
        "Oscillator1_Transpose": "Oct",
        "Oscillator1_Shape": "Shape",
        "Oscillator1_ShapeModSource": "Shape Mod",
        "Oscillator1_ShapeMod": "Shape Mod Amount",
        "Oscillator2_Type": "Osc 2",
        "Oscillator2_Transpose": "Oct",
        "Oscillator2_Detune": "Detune",
        "Oscillator1_Pitch_Detune": "Detune",
        "Oscillator1_Pitch_Transpose": "Transpose",
        "Oscillator1_Wavetables_WavePosition": "Position",
        "Oscillator2_Pitch_Detune": "Detune",
        "Oscillator2_Pitch_Transpose": "Transpose",
        "Oscillator2_Wavetables_WavePosition": "Position",
        "SubOscillator_Tone": "Tone",
        "SubOscillator_Transpose": "Transpose",
        "PitchModulation_Source1": "Source",
        "PitchModulation_Amount1": "Amount",
        "PitchModulation_Source2": "Source",
        "PitchModulation_Amount2": "Amount",

        # FX
        "Oscillator1_Effects_EffectMode": "Effects Mode",
        "Oscillator1_Effects_Effect1": "FX 1",
        "Oscillator1_Effects_Effect2": "FX 2",
        "Oscillator2_Effects_EffectMode": "Effects Mode",
        "Oscillator2_Effects_Effect1": "FX 1",
        "Oscillator2_Effects_Effect2": "FX 2",

        # Mixer
        "Oscillator1_On": "On/Off",
        "Oscillator1_Gain": "Gain",
        "Oscillator1_Pan": "Pan",
        "Oscillator2_On": "On/Off",
        "Oscillator2_Gain": "Gain",
        "Oscillator2_Pan": "Pan",
        "SubOscillator_On": "On/Off",
        "SubOscillator_Gain": "Gain",

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
        "Lfo_ModSource": "LFO Mod",
        "Lfo_ModAmount": "Mod Amount",
        "Lfo_AttackTime": "Attack",
        "Lfo_PhaseOffset": "Offset",
        "Lfo_Shaping": "Shape",
        "Lfo_Sync": "Sync Type",

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
        "Global_ResetOscillatorPhase": "Reset Osc Phase",
        "Global_HiQuality": "HQ",
        "Global_SerialNumber": "Serial",
        "Voice_Global_Glide": "Glide",
        "Voice_Global_Transpose": "Transpose",
        "Voice_Unison_Mode": "Unison",
        "Voice_Unison_Amount": "Amount",
        "Voice_Unison_VoiceCount": "Voices",

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

    # Parameters that should display without a text label.  This keeps the
    # interface compact for groups of related controls.
    UNLABELED_PARAMS = {
        "Voice_Filter1_On",
        "Voice_Filter1_Type",
        "Voice_Filter1_Slope",
        "Voice_Filter2_On",
        "Voice_Filter2_Type",
        "Voice_Filter2_Slope",
    }

    # Parameters that use a horizontal slider instead of a dial.
    SLIDER_PARAMS = {
        "Voice_Modulators_TimeScale",
        "Voice_Modulators_Lfo1_Time_Rate",
        "Voice_Modulators_Lfo2_Time_Rate",
        "Voice_Global_Glide",
        "Voice_Global_Transpose",
    }

    # Parameters that should not be displayed in the UI.
    HIDDEN_PARAMS = {
        "Voice_Modulators_Amount",
        "Voice_Modulators_TimeScale",
    }

    def _friendly_label(self, name: str) -> str:
        """Return a friendlier version of a parameter name."""
        if not name:
            return name
        label = name.replace("_", " ")
        label = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", label)
        label = re.sub(r"([a-z])([A-Z])", r"\1 \2", label)
        return label

    def _strip_qualifiers(self, name: str) -> str:
        """Remove common qualifier prefixes from a parameter name."""
        prefixes = [
            "Times_",
            "Values_",
            "Slopes_",
            "Time_",
            "Shape_",
        ]
        changed = True
        while changed:
            changed = False
            for p in prefixes:
                if name.startswith(p):
                    name = name[len(p) :]
                    changed = True
        return name

    def _build_param_item(self, idx, name, value, meta, label=None,
                           hide_label=False, slider=False, extra_classes=""):
        """Create HTML for a single parameter control."""
        p_type = meta.get("type")
        label = label if label is not None else self.LABEL_OVERRIDES.get(
            name, self._friendly_label(name)
        )

        classes = "param-item"
        if extra_classes:
            classes += f" {extra_classes}"
        html = [f'<div class="{classes}" data-name="{name}">']
        if not hide_label:
            html.append(f'<span class="param-label">{label}</span>')

        if p_type == "enum" and meta.get("options"):
            select_class = "param-select"
            if re.match(r"Voice_Filter[12]_Type", name):
                select_class += " filter-type-select"
            html.append(f'<select class="{select_class}" name="param_{idx}_value">')
            for opt in meta["options"]:
                sel = " selected" if str(value) == str(opt) else ""
                disp = opt
                if name.endswith("_Slope"):
                    disp = f"{opt}-pole"
                html.append(f'<option value="{opt}"{sel}>{disp}</option>')
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
                dec_attr = f' data-decimals="{decimals}"' if decimals is not None else ''
                disp_id = f'param_{idx}_display'
                input_classes = "param-dial input-knob"
                extra_attrs = ""
                if name == "Filter_Frequency":
                    input_classes += " filter-knob"
                    extra_attrs += ' data-diameter="48"'
                if "SyncedRate" in name:
                    step_attr = ' step="1"'
                    dec_attr = ' data-decimals="0"'
                    extra_attrs += f' data-values="{",".join(SYNC_RATE_LABELS)}"'
                html.append(
                    f'<input id="param_{idx}_dial" type="range" class="{input_classes}" data-target="param_{idx}_value" '
                    f'data-display="{disp_id}" value="{value}"{min_attr}{max_attr}{step_attr}{unit_attr}{dec_attr}{extra_attrs}>'
                )
                html.append(f'<span id="{disp_id}" class="param-number"></span>')
                html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')

        html.append(f'<input type="hidden" name="param_{idx}_name" value="{name}">')
        html.append('</div>')
        return ''.join(html)

    def _get_section(self, name):
        """Return the panel section for a raw Wavetable parameter name."""
        if name == "Voice_Global_FilterRouting":
            return "Filter"
        if name.startswith(("Voice_Oscillator1_Effects_", "Voice_Oscillator2_Effects_")):
            return "FX"
        if re.search(r"Voice_(?:Oscillator[12]|SubOscillator)_(?:On|Gain|Pan)$", name):
            return "Mixer"
        if name.startswith(("Voice_Oscillator", "Voice_SubOscillator")):
            return "Oscillators"
        if name.startswith("Voice_Filter"):
            return "Filter"
        if name.startswith("Voice_Modulators_AmpEnvelope") or name.startswith("Voice_Modulators_Envelope"):
            return "Envelopes"
        if name.startswith("Voice_Modulators_Lfo"):
            return "Modulation"
        if name.startswith("Voice_Modulators"):
            return "Modulation"
        if name.startswith(("Voice_Global_", "Voice_Unison_")) or name in {"HiQ", "MonoPoly", "PolyVoices", "Volume"}:
            return "Global"
        return "Other"

    def _arrange_filter_panel(self, items: dict) -> list:
        """Return filter panel HTML arranged into a single row."""
        ordered = []
        sample = next(iter(items.values()), "")
        match = re.search(r"Voice_Filter(\d)_", sample)
        idx = match.group(1) if match else "1"

        on = items.pop("On", "")
        f_type = items.pop("Type", "")
        slope = items.pop("Slope", "")
        freq = items.pop("Frequency", "")
        res = items.pop("Resonance", "")
        drive = items.pop("Drive", "")
        morph = items.pop("Morph", "")

        stack = "".join([on, f_type, slope])
        column = f'<div class="param-column">{stack}</div>' if stack.strip() else ""

        if drive:
            drive = drive.replace(
                'param-item',
                f'param-item filter-drive filter{idx}-drive hidden',
                1,
            )

        if morph:
            morph = morph.replace(
                'param-item',
                f'param-item filter-morph filter{idx}-morph hidden',
                1,
            )

        row = f"{column}{freq}{res}{drive}{morph}"
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')

        items.pop("CircuitBpNoMo", None)
        items.pop("CircuitLpHp", None)

        if items:
            ordered.extend(items.values())
        return ordered

    def _arrange_osc_panel(self, items: dict, sprite_html: str) -> list:
        """Return oscillator panel rows including sprite selection."""
        ordered = []
        row = "".join([
            sprite_html,
            items.pop("Pitch_Detune", ""),
            items.pop("Pitch_Transpose", ""),
            items.pop("Wavetables_WavePosition", ""),
        ])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')

        fx_row = "".join([
            items.pop("EffectMode", ""),
            items.pop("Effect1", ""),
            items.pop("Effect2", ""),
        ])

        if items:
            ordered.extend(items.values())

        if fx_row.strip():
            ordered.append(f'<div class="param-row">{fx_row}</div>')

        return ordered

    def _arrange_sub_panel(self, items: dict) -> list:
        """Return sub oscillator panel rows."""
        ordered = []
        row = "".join([
            items.pop("Tone", ""),
            items.pop("Transpose", ""),
        ])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        if items:
            ordered.extend(items.values())
        return ordered

    def _arrange_fx_panel(self, items: dict) -> list:
        """Return FX panel rows for an oscillator."""
        ordered = []
        row = "".join([
            items.pop("EffectMode", ""),
            items.pop("Effect1", ""),
            items.pop("Effect2", ""),
        ])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        if items:
            ordered.extend(items.values())
        return ordered

    def _arrange_mixer_panel(self, items: dict, include_pan: bool = True) -> list:
        """Return mixer panel rows for an oscillator."""
        ordered = []
        parts = [
            items.pop("On", ""),
            items.pop("Gain", ""),
        ]
        if include_pan:
            parts.append(items.pop("Pan", ""))
        row = "".join(parts)
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        if items:
            ordered.extend(items.values())
        return ordered

    def _arrange_envelope_panel(self, items: dict, canvas_id: str = None) -> list:
        """Return envelope panel rows with ADSR ordering and optional canvas."""
        ordered = []

        row = "".join(
            [
                items.pop("Attack", ""),
                items.pop("Sustain", ""),
                items.pop("Decay", ""),
                items.pop("Release", ""),
            ]
        )

        loop = items.pop("LoopMode", "")
        initial_val = items.pop("Initial", "")
        peak_val = items.pop("Peak", "")
        final_val = items.pop("Final", "")

        second_row = "".join([loop, initial_val, peak_val, final_val])

        rows = []
        if row.strip():
            rows.append(f'<div class="param-row">{row}</div>')
        if second_row.strip():
            rows.append(f'<div class="param-row">{second_row}</div>')

        if canvas_id:
            canvas = (
                f'<canvas id="{canvas_id}" '
                f'class="adsr-canvas env-visualization" width="200" height="88"></canvas>'
            )
            ordered.append(
                f'<div class="env-container"><div class="env-controls">{"".join(rows)}</div>{canvas}</div>'
            )
        else:
            ordered.extend(rows)

        if items:
            ordered.extend(items.values())
        return ordered

    def _arrange_lfo_panel(self, items: dict, idx: int | None = None) -> list:
        """Return LFO panel rows with a visualization canvas."""
        ordered = []
        canvas_id = f"lfo{idx}-canvas" if idx else "lfo-canvas"
        ordered.append(
            f'<canvas id="{canvas_id}" class="lfo-canvas" width="300" height="88"></canvas>'
        )

        rate = items.pop("Rate", "")
        sync_rate = items.pop("SyncedRate", "")
        sync = items.pop("Sync", "")
        row1 = "".join([rate, sync_rate, sync])
        if row1.strip():
            ordered.append(f'<div class="param-row lfo-rate-row">{row1}</div>')

        row2 = "".join([
            items.pop("Type", ""),
            items.pop("AttackTime", ""),
            items.pop("Retrigger", ""),
        ])
        if row2.strip():
            ordered.append(f'<div class="param-row">{row2}</div>')

        row3 = "".join([
            items.pop("Amount", ""),
            items.pop("Shaping", ""),
            items.pop("PhaseOffset", ""),
        ])
        if row3.strip():
            ordered.append(f'<div class="param-row">{row3}</div>')

        items.pop("UnifiedRateModulation", None)

        if items:
            ordered.extend(items.values())
        return ordered

    def _arrange_sub_column(self, osc_items: dict, mixer_items: dict) -> list:
        """Return stacked rows for the Sub oscillator."""
        ordered = []
        for key in ("On", "Gain"):
            val = mixer_items.pop(key, "")
            if val.strip():
                ordered.append(f'<div class="param-row">{val}</div>')
        for key in ("Tone", "Transpose"):
            val = osc_items.pop(key, "")
            if val.strip():
                ordered.append(f'<div class="param-row">{val}</div>')
        if mixer_items:
            ordered.extend(mixer_items.values())
        if osc_items:
            ordered.extend(osc_items.values())
        return ordered

    def _arrange_osc_column(
        self,
        osc_items: dict,
        mixer_items: dict,
        fx_items: dict,
        sprite_html: str,
    ) -> list:
        """Return ordered rows for an oscillator column."""
        ordered = []
        row = "".join([mixer_items.pop("On", ""), sprite_html])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        row = "".join(
            [
                mixer_items.pop("Pan", ""),
                mixer_items.pop("Gain", ""),
                osc_items.pop("Wavetables_WavePosition", ""),
            ]
        )
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        row = "".join(
            [
                osc_items.pop("Pitch_Detune", ""),
                osc_items.pop("Pitch_Transpose", ""),
            ]
        )
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        fx_row = "".join(
            [
                fx_items.pop("EffectMode", ""),
                fx_items.pop("Effect1", ""),
                fx_items.pop("Effect2", ""),
            ]
        )
        if mixer_items:
            ordered.extend(mixer_items.values())
        if fx_items:
            ordered.extend(fx_items.values())
        if osc_items:
            ordered.extend(osc_items.values())
        if fx_row.strip():
            ordered.append(f'<div class="param-row">{fx_row}</div>')
        return ordered

    def _arrange_global_panel(self, items: dict) -> list:
        """Return ordered rows for the Global panel."""
        ordered = []
        row = "".join([
            items.pop("HiQ", ""),
            items.pop("Volume", ""),
        ])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        row = "".join([
            items.pop("Glide", ""),
            items.pop("Transpose", ""),
        ])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        row = "".join([
            items.pop("MonoPoly", ""),
            items.pop("PolyVoices", ""),
        ])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        row = "".join([
            items.pop("Mode", ""),
            items.pop("Amount", ""),
            items.pop("VoiceCount", ""),
        ])
        if row.strip():
            ordered.append(f'<div class="param-row">{row}</div>')
        if items:
            ordered.extend(items.values())
        return ordered

    def generate_params_html(self, params, mapped_parameters=None):
        """Return HTML controls for the given parameter values."""
        if not params:
            return '<p>No parameters found.</p>'

        if mapped_parameters is None:
            mapped_parameters = {}

        schema = load_wavetable_schema()
        fx_modes = {1: 'None', 2: 'None'}
        for item in params:
            n = item.get('name')
            if n == 'Voice_Oscillator1_Effects_EffectMode':
                fx_modes[1] = item.get('value')
            elif n == 'Voice_Oscillator2_Effects_EffectMode':
                fx_modes[2] = item.get('value')
        sections = {s: [] for s in self.SECTION_ORDER}
        subgroups = {
            sec: {lbl: {} for _, lbl, _ in self.SECTION_SUBPANELS.get(sec, [])}
            for sec in self.SECTION_SUBPANELS
        }
        global_items = {}

        for i, item in enumerate(params):
            name = item["name"]
            val = item["value"]
            meta = dict(schema.get(name, {}))
            if name in self.HIDDEN_PARAMS:
                continue
            if name in {
                "Voice_Oscillator1_Effects_Effect1",
                "Voice_Oscillator1_Effects_Effect2",
                "Voice_Oscillator2_Effects_Effect1",
                "Voice_Oscillator2_Effects_Effect2",
            }:
                meta.setdefault("unit", "%")

            hide = name in self.UNLABELED_PARAMS
            slider = name in self.SLIDER_PARAMS
            extra = ""
            if name in mapped_parameters:
                macro_idx = mapped_parameters[name]["macro_index"]
                extra = f"macro-{macro_idx}"

            sec = self._get_section(name)

            assigned = False
            if sec in self.SECTION_SUBPANELS:
                for prefix, panel_lbl, ov_prefix in self.SECTION_SUBPANELS[sec]:
                    if name.startswith(prefix):
                        base = name[len(prefix) :]
                        base = self._strip_qualifiers(base)
                        label_override = self.LABEL_OVERRIDES.get(
                            f"{ov_prefix}_{base}", self._friendly_label(base)
                        )
                        if ov_prefix.startswith("Oscillator") and base in {"Effect1", "Effect2"}:
                            idx = 1 if ov_prefix.startswith("Oscillator1") else 2
                            labels = {
                                "None": ("FX 1", "FX 2"),
                                None: ("FX 1", "FX 2"),
                                "Fm": ("Tune", "Amt"),
                                "Classic": ("PW", "Sync"),
                                "Modern": ("Warp", "Fold"),
                            }
                            mode = fx_modes.get(idx, "None")
                            label_override = labels.get(mode, labels["None"])[0 if base == "Effect1" else 1]
                        html = self._build_param_item(
                            i,
                            name,
                            val,
                            meta,
                            label=label_override,
                            hide_label=hide,
                            slider=slider,
                            extra_classes=extra,
                        )
                        subgroups[sec][panel_lbl][base] = html
                        assigned = True
                        break

            if not assigned:
                html = self._build_param_item(
                    i,
                    name,
                    val,
                    meta,
                    hide_label=hide,
                    slider=slider,
                    extra_classes=extra,
                )
                if sec == "Global":
                    base = name
                    if base.startswith("Voice_Global_"):
                        base = base[len("Voice_Global_") :]
                    elif base.startswith("Voice_Unison_"):
                        base = base[len("Voice_Unison_") :]
                    elif base.startswith("Global_"):
                        base = base[len("Global_") :]
                    base = self._strip_qualifiers(base)
                    global_items[base] = html
                else:
                    sections.setdefault(sec, []).append(html)

        for sec, groups in self.SECTION_SUBPANELS.items():
            if sec in {"Oscillators", "FX", "Mixer"}:
                continue
            group_items = []
            for _prefix, label, _ in groups:
                items = subgroups.get(sec, {}).get(label)
                if items:
                    group_items.append(
                        f'<div class="param-group-label">{label}</div>'
                    )
                    if sec == "Filter":
                        group_items.extend(self._arrange_filter_panel(items))
                    elif sec == "Envelopes":
                        canvas_map = {
                            "Amp Envelope": "amp-env-canvas",
                            "Envelope 2": "env2-canvas",
                            "Envelope 3": "env3-canvas",
                        }
                        cid = canvas_map.get(label)
                        group_items.extend(self._arrange_envelope_panel(items, cid))
                    elif sec == "Modulation" and label.startswith("LFO"):
                        m = re.search(r"LFO\s*(\d)", label)
                        idx = int(m.group(1)) if m else None
                        group_items.extend(self._arrange_lfo_panel(items, idx))
                    else:
                        group_items.extend(items.values())
            if sections.get(sec):
                group_items.extend(sections[sec])
            if group_items:
                sections[sec] = group_items

        sections["Global"] = self._arrange_global_panel(global_items)

        # Custom top panels for Sub and Oscillators
        sub_items = subgroups.get("Oscillators", {}).get("Sub Oscillator", {})
        sub_mixer = subgroups.get("Mixer", {}).get("Sub Oscillator", {})
        osc1_items = subgroups.get("Oscillators", {}).get("Oscillator 1", {})
        osc1_mixer = subgroups.get("Mixer", {}).get("Oscillator 1", {})
        osc1_fx = subgroups.get("FX", {}).get("Oscillator 1", {})
        osc2_items = subgroups.get("Oscillators", {}).get("Oscillator 2", {})
        osc2_mixer = subgroups.get("Mixer", {}).get("Oscillator 2", {})
        osc2_fx = subgroups.get("FX", {}).get("Oscillator 2", {})

        sub_panel = ''.join(self._arrange_sub_column(sub_items, sub_mixer))
        osc1_sprite = (
            '<div class="param-item"><span class="param-label">Osc 1</span>'
            '<select id="sprite1-cat" class="param-select"></select>'
            '<select id="sprite1-select" class="param-select"></select>'
            '<input type="hidden" name="sprite1" id="sprite1-input"></div>'
        )
        osc1_panel = ''.join(
            self._arrange_osc_column(osc1_items, osc1_mixer, osc1_fx, osc1_sprite)
        )
        osc2_sprite = (
            '<div class="param-item"><span class="param-label">Osc 2</span>'
            '<select id="sprite2-cat" class="param-select"></select>'
            '<select id="sprite2-select" class="param-select"></select>'
            '<input type="hidden" name="sprite2" id="sprite2-input"></div>'
        )
        osc2_panel = ''.join(
            self._arrange_osc_column(osc2_items, osc2_mixer, osc2_fx, osc2_sprite)
        )

        filter_panel = ''
        filter_items = sections.pop("Filter", None)
        if filter_items:
            filter_panel = (
                f'<div class="param-panel filter"><h3>Filter</h3>'
                f'<div class="param-items">{"".join(filter_items)}</div></div>'
            )

        top_panels = [
            f'<div class="param-panel sub"><h3>Sub</h3><div class="param-items">{sub_panel}</div></div>',
            f'<div class="param-panel oscillator-1"><h3>Oscillator 1</h3><div class="param-items">{osc1_panel}</div></div>',
            f'<div class="param-panel oscillator-2"><h3>Oscillator 2</h3><div class="param-items">{osc2_panel}</div></div>',
        ]
        if filter_panel:
            top_panels.append(filter_panel)

        custom_top = '<div class="wavetable-param-panels">' + ''.join(top_panels) + '</div>'

        bottom_panels = []
        for sec in self.SECTION_ORDER:
            if sec in {"Oscillators", "FX", "Mixer"}:
                continue
            items = sections.get(sec)
            if not items:
                continue
            cls = sec.lower().replace(' ', '-').replace('+', '')
            panel_html = (
                f'<div class="param-panel {cls}"><h3>{sec}</h3>'
                f'<div class="param-items">{"".join(items)}</div></div>'
            )
            bottom_panels.append(panel_html)

        out_html = custom_top
        if bottom_panels:
            out_html += '<div class="wavetable-param-panels">'
            out_html += ''.join(bottom_panels)
            out_html += '</div>'
        return out_html

    def generate_macro_knobs_html(self, macros):
        """Return HTML for a row of macro value knobs."""
        if not macros:
            macros = []

        def friendly(name: str) -> str:
            """Return a human-friendly version of a parameter name."""
            if not name:
                return name
            parts = [
                re.sub(r"([a-z])([A-Z])", r"\1 \2",
                       re.sub(r"([A-Za-z])([0-9])", r"\1 \2", p))
                for p in name.split("_")
            ]
            return ": ".join(parts)

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
                    name = friendly(pname)
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

