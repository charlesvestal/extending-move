import cgi
import re
from handlers.base_handler import BaseHandler
from core.synth_preset_inspector_handler import (
    extract_macro_information,
    update_preset_macro_names,
    extract_available_parameters,
    update_preset_parameter_mappings,
    delete_parameter_mapping
)
from core.file_browser import list_directory as list_dir

class SynthPresetInspectorHandler(BaseHandler):
    def handle_get(self):
        """Initialize the synth macros with synth presets dropdown"""
        return {
            "message": "Select a Drift preset from the browser",
            "message_type": "info",
            "macros_html": "",
            "selected_preset": None,
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
                
                if new_name:  # Only update if a name was provided
                    # Create a single macro update
                    macro_updates = {macro_index: new_name}
                    
                    # Update the preset file with the new macro name
                    update_result = update_preset_macro_names(preset_path, macro_updates)
                    if not update_result['success']:
                        return self.format_error_response(update_result['message'])
                    
                    message = f"Saved name for Macro {macro_index}: {new_name}"
                else:
                    return self.format_error_response("No name provided for the macro")
            
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
                        if new_name:  # Only update if a name was provided
                            macro_updates[macro_index] = new_name
                
                # Update the preset file with the new macro names
                if macro_updates:
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
                        print(f"Found path for parameter {parameter_name}: {parameter_path}")
                    
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
            
            return {
                "message": message,
                "message_type": "success",
                "macros_html": macros_html,
                "selected_preset": preset_path,
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
        if preset_path:
            # Extract the preset path from the form value
            preset_select = self.form.getvalue('preset_select') if hasattr(self, 'form') else None
            if preset_select:
                # Get all parameters
                param_result = extract_available_parameters(preset_select)
                if param_result['success']:
                    all_parameters = param_result['parameters']
                    parameter_paths = param_result.get('parameter_paths', {})
                    
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
                    
                    print(f"Available parameters: {len(available_parameters)}, Mapped parameters: {len(mapped_parameters)}")
        
        html = '<div class="macros-container">'
        
        for macro in macros:
            html += f'<div class="macro-item">'
            html += f'<div class="macro-header">'
            html += f'<span>Macro {macro["index"]}:</span> '
            html += f'<input type="text" name="macro_{macro["index"]}_name" value="{macro["name"]}" class="macro-name-input">'
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
                html += f'<option value="{param}"{selected}>{param}</option>'
            
            html += '</select>'
            
            # Range inputs inline with Add button
            html += '<div class="range-inputs-inline">'
            html += f'<label>Min: <input type="number" name="macro_{macro["index"]}_range_min" value="{default_range_min}" step="any"></label>'
            html += f'<label>Max: <input type="number" name="macro_{macro["index"]}_range_max" value="{default_range_max}" step="any"></label>'
            
            # Add the "Add" button inline with range inputs
            html += f'<button type="submit" class="add-mapping-btn" '
            html += f'onclick="document.getElementById(\'action-input\').value=\'add_mapping\'; '
            html += f'document.getElementById(\'macro-index-input\').value=\'{macro["index"]}\';">'
            html += f'Add</button>'
            html += '</div>'
            
            html += '</div>'  # Close parameter-controls
            
            html += '</div>'
            
            # Display current mappings
            html += '<div class="current-mappings">'
            html += '<h4>Current Mappings:</h4>'
            
            if macro["parameters"]:
                html += '<ul class="parameters-list">'
                for param in macro["parameters"]:
                    param_info = f'{param["name"]}'
                    if "rangeMin" in param and "rangeMax" in param:
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
            
            html += '</div>'
            html += '</div>'
            
        html += '</div>'
        return html

    def list_directory(self, rel_path: str):
        """Return directories and preset files for a given relative path."""
        return list_dir(
            "/data/UserData/UserLibrary/Track Presets",
            rel_path,
            [".ablpreset"],
        )
    
