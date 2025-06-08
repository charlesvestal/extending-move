import re
import os
import logging
import json
from handlers.base_handler import BaseHandler
from core.synth_preset_inspector_handler import (
    scan_for_synth_presets, 
    extract_macro_information,
    update_preset_macro_names,
    extract_available_parameters,
    extract_parameter_values,
    update_preset_parameter_mappings,
    delete_parameter_mapping,
    load_drift_schema
)
from core.file_browser import generate_dir_html

logger = logging.getLogger(__name__)

class SynthPresetInspectorHandler(BaseHandler):
    def handle_get(self):
        """Return file browser for synth presets."""
        base_dir = "/data/UserData/UserLibrary/Track Presets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
            base_dir = "examples/Track Presets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            '/synth-macros',
            'preset_select',
            'select_preset',
            filter_key='drift'
        )
        schema = load_drift_schema()
        return {
            "message": "Select a Drift preset from the list",
            "message_type": "info",
            "file_browser_html": browser_html,
            "macros_html": "",
            "all_params_html": "",
            "selected_preset": None,
            "browser_root": base_dir,
            "browser_filter": 'drift',
            "schema_json": json.dumps(schema),
        }

    def handle_post(self, form):
        """Handle preset selection and editing"""
        # Store form for use in generate_macros_html
        self.form = form
        
        action = form.getvalue('action')
        if action == 'reset_preset':
            return self.handle_get()

        if action in ['select_preset', 'save_names', 'save_name', 'delete_mapping', 'add_mapping']:
            preset_path = form.getvalue('preset_select')
            if not preset_path:
                return self.format_error_response("No preset selected")
            
            # If this is a save name action for a single macro, update just that macro name
            if action == 'save_name':
                macro_index = int(form.getvalue('macro_index'))
                new_name = form.getvalue(f'macro_{macro_index}_name')

                # Allow blank names to remove customName
                macro_updates = {macro_index: new_name}

                # Update the preset file with the new macro name (or removal)
                update_result = update_preset_macro_names(preset_path, macro_updates)
                if not update_result['success']:
                    return self.format_error_response(update_result['message'])

                if new_name:
                    message = f"Saved name for Macro {macro_index}: {new_name}"
                else:
                    message = f"Removed custom name for Macro {macro_index}"
            
            # If this is a save names action for all macros, update all macro names
            elif action == 'save_names':
                # Extract macro name updates from the form
                macro_updates = {}
                for field_name in form.keys():
                    # Match fields like "macro_1_name", "macro_2_name", etc.
                    match = re.match(r'macro_(\d+)_name', field_name)
                    if match:
                        macro_index = int(match.group(1))
                        new_name = form.getvalue(field_name)
                        macro_updates[macro_index] = new_name

                update_result = update_preset_macro_names(preset_path, macro_updates)
                if not update_result['success']:
                    return self.format_error_response(update_result['message'])
                
                message = f"Saved macro names for preset: {preset_path.split('/')[-1]}"
            
            # If this is an add mapping action, add a single parameter mapping
            elif action == 'add_mapping':
                macro_index = int(form.getvalue('macro_index'))
                parameter_name = form.getvalue(f'macro_{macro_index}_parameter')
                
                # Only process if a parameter was selected
                if parameter_name:
                    # Get range values if provided
                    range_min = form.getvalue(f'macro_{macro_index}_range_min')
                    range_max = form.getvalue(f'macro_{macro_index}_range_max')
                    
                    # Get parameter path if available
                    parameter_path = None
                    if hasattr(self, 'parameter_paths') and parameter_name in self.parameter_paths:
                        parameter_path = self.parameter_paths[parameter_name]
                        logger.debug(
                            "Found path for parameter %s: %s", parameter_name, parameter_path
                        )
                    
                    # Create parameter update for just this one mapping
                    parameter_updates = {
                        macro_index: {
                            'parameter': parameter_name,
                            'parameter_path': parameter_path,
                            'rangeMin': range_min,
                            'rangeMax': range_max
                        }
                    }
                    
                    # Update the preset file with just this one mapping
                    update_result = update_preset_parameter_mappings(preset_path, parameter_updates)
                    if not update_result['success']:
                        return self.format_error_response(update_result['message'])
                    
                    message = f"Added mapping for parameter {parameter_name} to Macro {macro_index}"
                else:
                    return self.format_error_response("No parameter selected for mapping")
            
            # If this is a delete mapping action, delete the mapping
            elif action == 'delete_mapping':
                param_path = form.getvalue('param_path')
                param_name = form.getvalue('param_name')
                
                if not param_path:
                    return self.format_error_response("No parameter path provided")
                
                # Delete the mapping
                delete_result = delete_parameter_mapping(preset_path, param_path)
                if not delete_result['success']:
                    return self.format_error_response(delete_result['message'])
                
                message = f"Deleted mapping for parameter {param_name}"
            
            # Set message for select_preset action
            elif action == 'select_preset':
                message = f"Selected preset: {preset_path.split('/')[-1]}"
            
            # Extract macro information from the selected preset (potentially updated)
            macro_result = extract_macro_information(preset_path)
            if not macro_result['success']:
                return self.format_error_response(macro_result['message'])

            # Generate HTML for displaying macros
            macros_html = self.generate_macros_html(macro_result['macros'])

            # Get all parameters with their values
            all_params = extract_parameter_values(preset_path)
            if all_params['success']:
                all_params_html = self.generate_all_params_html(all_params['parameters'])
            else:
                all_params_html = f"<p>{all_params['message']}</p>"

            base_dir = "/data/UserData/UserLibrary/Track Presets"
            if not os.path.exists(base_dir) and os.path.exists("examples/Track Presets"):
                base_dir = "examples/Track Presets"
            browser_html = generate_dir_html(
                base_dir,
                "",
                '/synth-macros',
                'preset_select',
                'select_preset',
                filter_key='drift'
            )

            return {
                "message": message,
                "message_type": "success",
                "file_browser_html": browser_html,
                "macros_html": macros_html,
                "all_params_html": all_params_html,
                "selected_preset": preset_path,
                "browser_root": base_dir,
                "browser_filter": 'drift',
                "schema_json": json.dumps(self.parameter_info),
            }
        
        return self.format_info_response("Unknown action")
        
    def generate_macros_html(self, macros):
        """Generate HTML for displaying macros"""
        if not macros:
            return "<p>No macros found in this preset.</p>"
        
        # Get the preset path from the first macro's parameters (if any)
        preset_path = None
        for macro in macros:
            if macro["parameters"]:
                # Extract the preset path from the first parameter's path
                param_path = macro["parameters"][0]["path"]
                # The path will be something like "chains[0].devices[0].parameters.Filter_Frequency"
                # We need to extract the preset path from this
                preset_path = param_path.split(".parameters")[0]
                break
        
        # Get all available parameters for the dropdown
        available_parameters = []
        parameter_paths = {}
        mapped_parameters = {}
        self.parameter_info = {}
        if preset_path:
            # Extract the preset path from the form value
            preset_select = self.form.getvalue('preset_select') if hasattr(self, 'form') else None
            if preset_select:
                # Get all parameters
                param_result = extract_available_parameters(preset_select)
                if param_result['success']:
                    all_parameters = param_result['parameters']
                    parameter_paths = param_result.get('parameter_paths', {})
                    self.parameter_info = param_result.get('parameter_info', {})
                    
                    # Store parameter paths in the class for use in handle_post
                    self.parameter_paths = parameter_paths
                    
                    # Get mapped parameters
                    macro_result = extract_macro_information(preset_select)
                    if macro_result['success']:
                        mapped_parameters = macro_result.get('mapped_parameters', {})
                        
                        # Store mapped parameters in the class for use in handle_post
                        self.mapped_parameters = mapped_parameters
                        
                        # Filter out parameters that are already mapped to macros
                        available_parameters = [p for p in all_parameters if p not in mapped_parameters]
                    else:
                        available_parameters = all_parameters
                    
                    logger.debug(
                        "Available parameters: %d, Mapped parameters: %d",
                        len(available_parameters),
                        len(mapped_parameters),
                    )
        
        html = '<div class="macros-container">'

        for macro in macros:
            value = macro.get("value")
            try:
                value = float(value)
            except Exception:
                value = 0.0
            display_val = round(value, 1)
            html += f'<div class="macro-item macro-{macro["index"]}">'
            html += '<div class="macro-top">'
            name_label = macro.get("name", f"Macro {macro['index']}")
            html += (
                f'<div class="macro-knob macro-{macro["index"]}">'
                f'<span class="macro-label">{name_label}</span>'
                f'<input type="range" class="macro-dial input-knob" '
                f'value="{display_val}" min="0" max="127" step="0.1" data-decimals="1" disabled>'
                f'<span class="macro-number">{display_val}</span>'
                f'</div>'
            )
            html += '<div>'
            html += f'<div class="macro-header">'
            html += f'<span>Macro {macro["index"]}:</span> '
            default_label = f"Macro {macro['index']}"
            macro_value = macro["name"] if macro["name"] != default_label else ""
            placeholder = " placeholder=\"Default name chosen by Move..\"" if not macro_value else ""
            html += (
                f'<input type="text" name="macro_{macro["index"]}_name" '
                f'value="{macro_value}"{placeholder} class="macro-name-input">'
            )
            # Add the "Save Name" button
            html += f'<button type="submit" class="save-name-btn" '
            html += f'onclick="document.getElementById(\'action-input\').value=\'save_name\'; '
            html += f'document.getElementById(\'macro-index-input\').value=\'{macro["index"]}\';">'
            html += f'Save Name</button>'
            html += '</div>'
            
            # Default values are always blank for new mappings
            default_param = None
            default_range_min = ""
            default_range_max = ""
            
            # Add parameter selection dropdown and range inputs
            html += '<div class="parameter-mapping">'
            html += '<div class="parameter-controls">'
            
            # Parameter dropdown
            html += f'<label for="macro_{macro["index"]}_parameter">Map Parameter:</label>'
            html += f'<select name="macro_{macro["index"]}_parameter" id="macro_{macro["index"]}_parameter">'
            html += '<option value="">--Select Parameter--</option>'
            
            # Add options for all available parameters
            for param in available_parameters:
                selected = ' selected="selected"' if param == default_param else ''
                info = self.parameter_info.get(param, {})
                data_attrs = ''
                if info.get('type'):
                    data_attrs += f' data-type="{info["type"]}"'
                if info.get('min') is not None:
                    data_attrs += f' data-min="{info["min"]}"'
                if info.get('max') is not None:
                    data_attrs += f' data-max="{info["max"]}"'
                if info.get('options'):
                    opts = ",".join(map(str, info['options']))
                    data_attrs += f' data-options="{opts}"'
                html += f'<option value="{param}"{selected}{data_attrs}>{param}</option>'
            
            html += '</select>'
            
            # Range inputs inline with Add button
            html += (
                f'<label class="min-wrapper">Min: <input type="number" class="range-min" '
                f'name="macro_{macro["index"]}_range_min" value="{default_range_min}" step="any"></label>'
            )
            html += (
                f'<label class="max-wrapper">Max: <input type="number" class="range-max" '
                f'name="macro_{macro["index"]}_range_max" value="{default_range_max}" step="any"></label>'
            )
            html += '<div class="options-display"></div>'

            # Add the "Add" button
            html += f'<button type="submit" class="add-mapping-btn" '
            html += f'onclick="document.getElementById(\'action-input\').value=\'add_mapping\'; '
            html += f'document.getElementById(\'macro-index-input\').value=\'{macro["index"]}\';">'
            html += 'Add</button>'
            html += '</div>'  # Close parameter-controls

            html += '</div>'

            # Display current mappings
            html += '<div class="current-mappings">'
            html += '<h4>Current Mappings:</h4>'
            
            if macro["parameters"]:
                html += '<ul class="parameters-list">'
                for param in macro["parameters"]:
                    param_info = f'{param["name"]}'
                    info = self.parameter_info.get(param["name"], {})
                    if info.get("options"):
                        opts = ", ".join(map(str, info["options"]))
                        param_info += f' [Options: {opts}]'
                    elif "rangeMin" in param and "rangeMax" in param:
                        param_info += f' (Range: {param["rangeMin"]} - {param["rangeMax"]})'
                    
                    # Add delete button with onclick handler to set action and parameter info
                    html += f'<li class="parameter-item">'
                    html += f'<span class="parameter-info">{param_info}</span>'
                    html += f'<button type="submit" class="delete-mapping-btn" '
                    html += f'onclick="document.getElementById(\'action-input\').value=\'delete_mapping\'; '
                    html += f'document.getElementById(\'param-path-input\').value=\'{param["path"]}\'; '
                    html += f'document.getElementById(\'param-name-input\').value=\'{param["name"]}\';">'
                    html += f'Delete</button>'
                    html += f'</li>'
                html += '</ul>'
            else:
                html += '<p>No parameters mapped to this macro.</p>'
            
            html += '</div>'  # close current-mappings
            html += '</div>'  # close inner container
            html += '</div>'  # close macro-top
            html += '</div>'  # close macro-item
            
        html += '</div>'
        return html

    def get_preset_options(self, selected_preset=None):
        """Deprecated dropdown helper."""
        return ''

    def generate_all_params_html(self, parameters):
        """Return HTML list of all parameters and their values."""
        if not parameters:
            return "<p>No parameters found.</p>"
        html = '<ul class="all-params-list">'
        for item in parameters:
            html += f'<li>{item["name"]}: {item["value"]}</li>'
        html += '</ul>'
        return html
