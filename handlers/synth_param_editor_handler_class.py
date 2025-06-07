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
        "Oscillator",
        "Mixer",
        "Filter",
        "Envelopes",
        "LFO + Mod",
        "Global",
        "Other",
    ]

    def _get_section(self, name):
        if name.startswith(("Oscillator1_", "Oscillator2_", "PitchModulation_")):
            return "Oscillator"
        if name.startswith("Mixer_"):
            return "Mixer"
        if name.startswith("Filter_"):
            return "Filter"
        if name.startswith(("Envelope1_", "Envelope2_")):
            return "Envelopes"
        if name.startswith(("CyclingEnvelope_", "ModulationMatrix_")):
            return "LFO + Mod"
        if name.startswith("Global_"):
            return "Global"
        return "Other"

    def generate_params_html(self, params):
        """Return HTML controls for the given parameter values."""
        if not params:
            return '<p>No parameters found.</p>'

        schema = load_drift_schema()
        sections = {s: [] for s in self.SECTION_ORDER}

        for i, item in enumerate(params):
            name = item['name']
            val = item['value']
            meta = schema.get(name, {})
            p_type = meta.get('type')

            html = '<div class="param-item">'
            html += f'<label>{name}: '
            if p_type == 'enum' and meta.get('options'):
                html += f'<select name="param_{i}_value">'
                for opt in meta['options']:
                    selected = ' selected' if str(val) == str(opt) else ''
                    html += f'<option value="{opt}"{selected}>{opt}</option>'
                html += '</select>'
            else:
                min_attr = f' data-min="{meta.get("min")}"' if meta.get("min") is not None else ''
                max_attr = f' data-max="{meta.get("max")}"' if meta.get("max") is not None else ''
                val_attr = f' data-value="{val}"'
                unit_attr = f' data-unit="{meta.get("unit")}"' if meta.get("unit") else ''
                dec_attr = f' data-decimals="{meta.get("decimals")}"' if meta.get("decimals") is not None else ''
                display_id = f'param_{i}_display'
                html += (
                    f'<div id="param_{i}_dial" class="param-dial" data-target="param_{i}_value" data-display="{display_id}"{min_attr}{max_attr}{val_attr}{unit_attr}{dec_attr}></div>'
                )
                html += f'<span id="{display_id}" class="param-number"></span>'
                html += f'<input type="hidden" name="param_{i}_value" value="{val}">'
            html += '</label>'
            html += f'<input type="hidden" name="param_{i}_name" value="{name}">' 
            html += '</div>'

            section = self._get_section(name)
            sections[section].append(html)

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

