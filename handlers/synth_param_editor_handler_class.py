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

TARGET_PARAMS = [
    "Oscillator1_Transpose",
    "Oscillator1_Shape",
    "Oscillator2_Transpose",
    "Oscillator2_Detune",
    "Mixer_OscillatorGain1",
    "Mixer_OscillatorGain2",
    "Mixer_NoiseLevel",
    "Filter_Frequency",
    "Filter_Resonance",
    "Filter_HiPassFrequency",
    "Envelope1_Attack",
    "Envelope1_Sustain",
    "Envelope1_Decay",
    "Envelope1_Release",
    "Envelope2_Attack",
    "Envelope2_Sustain",
    "Envelope2_Decay",
    "Envelope2_Release",
    "Lfo_Ratio",
    "Lfo_Amount",
    "Global_Volume",
]


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
            params_html, param_count = self.generate_params_html(values['parameters'])

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

    def generate_params_html(self, params):
        """Return HTML controls for the selected parameter values."""
        if not params:
            return '<p>No parameters found.</p>', 0

        schema = load_drift_schema()
        html = '<div class="params-list">'
        idx = 0
        for item in params:
            name = item['name']
            if name not in TARGET_PARAMS:
                continue
            val = item['value']
            meta = schema.get(name, {})
            min_val = meta.get('min', 0)
            max_val = meta.get('max', 1)
            if min_val is not None and max_val is not None and -1 <= min_val and max_val <= 1:
                step = 0.01
            else:
                step = 1
            knob_id = f'knob_{idx}'
            html += '<div class="param-item">'
            html += f'<label for="{knob_id}">{name}</label>'
            html += (
                f'<div id="{knob_id}" class="nexus-knob" data-min="{min_val}" '
                f'data-max="{max_val}" data-step="{step}" data-target="param_{idx}_value" data-value="{val}"></div>'
            )
            html += f'<input type="hidden" name="param_{idx}_value" id="param_{idx}_value" value="{val}">' 
            html += f'<input type="hidden" name="param_{idx}_name" value="{name}">' 
            html += '</div>'
            idx += 1
        html += '</div>'
        return html, idx

