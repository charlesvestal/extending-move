#!/usr/bin/env python3
import os
import json
import logging
import shutil

from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.synth_preset_inspector_handler import (
    extract_parameter_values,
    load_melodic_sampler_schema,
    extract_macro_information,
    update_preset_macro_names,
    update_preset_parameter_mappings,
    delete_parameter_mapping,
    extract_available_parameters,
)
from core.synth_param_editor_handler import (
    update_parameter_values,
    update_macro_values,
)
from core.refresh_handler import refresh_library

DEFAULT_PRESET = os.path.join(
    "/data/UserData/UserLibrary/Track Presets",
    "melodicSampler",
    "Ac Piano Grand.ablpreset",
)
if not os.path.exists(DEFAULT_PRESET):
    DEFAULT_PRESET = os.path.join(
        "examples",
        "Track Presets",
        "melodicSampler",
        "Ac Piano Grand.ablpreset",
    )

NEW_PRESET_DIR = os.path.join(
    "/data/UserData/UserLibrary/Track Presets",
    "melodicSampler",
)

CORE_LIBRARY_DIR = "/data/CoreLibrary/Track Presets"

logger = logging.getLogger(__name__)

EXCLUDED_MACRO_PARAMS = set()

DEFAULT_MACRO_NAMES = ["A", "B", "C", "D", "E", "F", "G", "H"]
DEFAULT_MACRO_PARAMS = [
    "Voice_AmplitudeEnvelope_Attack",
    "Voice_AmplitudeEnvelope_Decay",
    "Voice_AmplitudeEnvelope_Release",
    "Voice_AmplitudeEnvelope_Sustain",
    "Voice_Detune",
    "Voice_FilterEnvelope_Attack",
    "Voice_FilterEnvelope_Decay",
    "Voice_FilterEnvelope_Release",
]

class MelodicSamplerParamEditorHandler(BaseHandler):
    def handle_get(self):
        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/melodic-sampler',
            'preset_select',
            'select_preset',
            filter_key='melodicsampler',
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        schema = load_melodic_sampler_schema()
        return {
            'message': 'Select a Melodic Sampler preset from the list or create a new one',
            'message_type': 'info',
            'file_browser_html': browser_html,
            'params_html': '',
            'selected_preset': None,
            'param_count': 0,
            'browser_root': base_dir,
            'browser_filter': 'melodicsampler',
            'schema_json': json.dumps(schema),
            'default_preset_path': DEFAULT_PRESET,
            'macro_knobs_html': '',
            'rename_checked': False,
            'macros_json': '[]',
            'available_params_json': '[]',
            'param_paths_json': '{}',
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
                device_types=("melodicSampler",),
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

            name_updates = {i: DEFAULT_MACRO_NAMES[i] for i in range(8)}
            name_result = update_preset_macro_names(preset_path, name_updates)
            if not name_result['success']:
                return self.format_error_response(name_result['message'])

            param_info = extract_available_parameters(
                preset_path,
                device_types=("melodicSampler",),
                schema_loader=load_melodic_sampler_schema,
            )
            paths = param_info.get('parameter_paths', {}) if param_info['success'] else {}
            param_updates = {
                i: {
                    'parameter': DEFAULT_MACRO_PARAMS[i],
                    'parameter_path': paths.get(DEFAULT_MACRO_PARAMS[i]),
                }
                for i in range(8)
            }
            map_result = update_preset_parameter_mappings(preset_path, param_updates)
            if not map_result['success']:
                return self.format_error_response(map_result['message'])

            existing_info = extract_macro_information(preset_path)
            existing_mapped = existing_info.get('mapped_parameters', {}) if existing_info['success'] else {}
            for pname, info in existing_mapped.items():
                if pname not in DEFAULT_MACRO_PARAMS:
                    delete_parameter_mapping(preset_path, info['path'])

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

        values = extract_parameter_values(preset_path, device_types=("melodicSampler",))
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
                    mc['name'] = ''
                macros_for_json.append(mc)
            macros_json = json.dumps(macros_for_json)

        param_info = extract_available_parameters(
            preset_path,
            device_types=("melodicSampler",),
            schema_loader=load_melodic_sampler_schema,
        )
        if param_info['success']:
            params = [p for p in param_info['parameters'] if p not in EXCLUDED_MACRO_PARAMS]
            paths = {k: v for k, v in param_info.get('parameter_paths', {}).items() if k not in EXCLUDED_MACRO_PARAMS}
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
            '/melodic-sampler',
            'preset_select',
            'select_preset',
            filter_key='melodicsampler',
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        return {
            'message': message,
            'message_type': 'success',
            'file_browser_html': browser_html,
            'params_html': params_html,
            'selected_preset': preset_path,
            'param_count': param_count,
            'browser_root': base_dir,
            'browser_filter': 'melodicsampler',
            'schema_json': json.dumps(load_melodic_sampler_schema()),
            'default_preset_path': DEFAULT_PRESET,
            'macro_knobs_html': macro_knobs_html,
            'rename_checked': rename_flag if action == 'save_params' else is_core,
            'macros_json': macros_json,
            'available_params_json': available_params_json,
            'param_paths_json': param_paths_json,
        }

    def _build_param_item(self, idx, name, value, meta, label=None, hide_label=False, slider=False, extra_classes=""):
        p_type = meta.get('type')
        label = label if label is not None else name
        classes = 'param-item'
        if extra_classes:
            classes += f' {extra_classes}'
        html = [f'<div class="{classes}" data-name="{name}">']
        if not hide_label:
            html.append(f'<span class="param-label">{label}</span>')
        if p_type == 'enum' and meta.get('options'):
            html.append(f'<select class="param-select" name="param_{idx}_value">')
            for opt in meta['options']:
                sel = ' selected' if str(value) == str(opt) else ''
                html.append(f'<option value="{opt}"{sel}>{opt}</option>')
            html.append('</select>')
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
        elif p_type == 'boolean':
            bool_val = 1 if str(value).lower() in ('true', '1') else 0
            checked = 'checked' if bool_val else ''
            html.append(
                f'<input type="checkbox" id="param_{idx}_toggle" class="param-toggle input-switch" '
                f'data-target="param_{idx}_value" data-true-value="1" data-false-value="0" {checked}>'
            )
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{bool_val}">')
        else:
            min_val = meta.get('min')
            max_val = meta.get('max')
            decimals = meta.get('decimals')
            step_val = meta.get('step')
            if decimals is not None and step_val is None:
                step_val = 10 ** (-decimals)
            if step_val is None and min_val is not None and max_val is not None and max_val <= 1 and min_val >= -1:
                step_val = 0.01
            unit_val = meta.get('unit')
            min_attr = f' min="{min_val}"' if min_val is not None else ''
            max_attr = f' max="{max_val}"' if max_val is not None else ''
            step_attr = f' step="{step_val}"' if step_val is not None else ''
            unit_attr = f' data-unit="{unit_val}"' if unit_val else ''
            dec_attr = f' data-decimals="{decimals}"' if decimals is not None else ''
            disp_id = f'param_{idx}_display'
            input_classes = 'param-dial input-knob'
            html.append(
                f'<input id="param_{idx}_dial" type="range" class="{input_classes}" data-target="param_{idx}_value" '
                f'data-display="{disp_id}" value="{value}"{min_attr}{max_attr}{step_attr}{unit_attr}{dec_attr}>'
            )
            html.append(f'<span id="{disp_id}" class="param-number"></span>')
            html.append(f'<input type="hidden" name="param_{idx}_value" value="{value}">')
        html.append(f'<input type="hidden" name="param_{idx}_name" value="{name}">')
        html.append('</div>')
        return ''.join(html)

    def generate_params_html(self, params, mapped_parameters=None):
        if not params:
            return '<p>No parameters found.</p>'
        if mapped_parameters is None:
            mapped_parameters = {}
        schema = load_melodic_sampler_schema()
        items = []
        for i, item in enumerate(params):
            name = item['name']
            val = item['value']
            meta = dict(schema.get(name, {}))
            extra = ''
            if name in mapped_parameters:
                macro_idx = mapped_parameters[name]['macro_index']
                extra = f'macro-{macro_idx}'
            items.append(self._build_param_item(i, name, val, meta, extra_classes=extra))
        return '<div class="param-panel"><div class="param-items">' + ''.join(items) + '</div></div>'


    def generate_macro_knobs_html(self, macros):
        values = {m.get('index'): m.get('value', 0.0) for m in (macros or [])}
        html = ['<div class="macro-knob-row">']
        for i in range(8):
            val = values.get(i, 0.0)
            try:
                val = float(val)
            except Exception:
                val = 0.0
            display_val = round(val, 1)
            name = DEFAULT_MACRO_NAMES[i]
            html.append(
                f'<div class="macro-knob" data-index="{i}">' +
                f'<span class="macro-label" data-index="{i}">{name}</span>' +
                f'<input id="macro_{i}_dial" type="range" class="macro-dial input-knob" ' +
                f'data-target="macro_{i}_value" data-display="macro_{i}_disp" ' +
                f'value="{display_val}" min="0" max="127" step="0.1" data-decimals="1">' +
                f'<span id="macro_{i}_disp" class="macro-number"></span>' +
                f'<input type="hidden" name="macro_{i}_value" value="{display_val}">' +
                '</div>'
            )
        html.append('</div>')
        return ''.join(html)
