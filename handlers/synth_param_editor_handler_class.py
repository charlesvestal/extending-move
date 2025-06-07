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
    ACTION_URL = "/synth-params"

    def handle_get(self):
        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            self.ACTION_URL,
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
            self.ACTION_URL,
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
        """Return HTML controls for the given parameter values."""
        if not params:
            return '<p>No parameters found.</p>'

        schema = load_drift_schema()
        html = '<div class="params-list">'
        for i, item in enumerate(params):
            name = item['name']
            val = item['value']
            meta = schema.get(name, {})
            p_type = meta.get('type')
            html += '<div class="param-item">'
            html += f'<label>{name}: '
            if p_type == 'enum' and meta.get('options'):
                html += f'<select name="param_{i}_value">'
                for opt in meta['options']:
                    selected = ' selected' if str(val) == str(opt) else ''
                    html += f'<option value="{opt}"{selected}>{opt}</option>'
                html += '</select>'
            else:
                # Numeric slider + input with dynamic step handling
                min_attr = f' min="{meta.get("min")}"' if meta.get("min") is not None else ''
                max_attr = f' max="{meta.get("max")}"' if meta.get("max") is not None else ''

                step_input = "any"
                if isinstance(val, (int, float)):
                    val_str = str(val)
                    if "." in val_str:
                        digits = len(val_str.split(".")[1].rstrip("0"))
                        if digits:
                            step_input = str(10 ** -digits)
                        else:
                            step_input = "1"
                    else:
                        step_input = "1"

                step_slider = step_input
                rng_min = meta.get("min")
                rng_max = meta.get("max")
                if rng_min is not None and rng_max is not None:
                    if -1 <= rng_min and rng_max <= 1:
                        if step_slider == "any" or float(step_slider) > 0.01:
                            step_slider = "0.01"
                if step_input == "1" and step_slider != "any":
                    step_input = step_slider
                slider_step_attr = f' step="{step_slider}"' if step_slider != "any" else ' step="any"'
                input_step_attr = f' step="{step_input}"' if step_input != "any" else ' step="any"'
                html += (
                    f'<input type="range" name="param_{i}_slider" value="{val}"{min_attr}{max_attr}{slider_step_attr} '
                    f'oninput="this.nextElementSibling.value=this.value">'
                )
                html += (
                    f'<input type="number" name="param_{i}_value" value="{val}"{min_attr}{max_attr}{input_step_attr} '
                    f'oninput="this.previousElementSibling.value=this.value">'
                )
            html += '</label>'
            html += f'<input type="hidden" name="param_{i}_name" value="{name}">' 
            html += '</div>'
        html += '</div>'
        return html

