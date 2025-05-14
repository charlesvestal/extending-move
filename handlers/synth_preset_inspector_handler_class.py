import cgi
import re
from handlers.base_handler import BaseHandler
from core.synth_preset_inspector_handler import scan_for_drift_presets, extract_macro_information, update_preset_macro_names

class SynthPresetInspectorHandler(BaseHandler):
    def handle_get(self):
        """Initialize the synth preset inspector with Drift presets dropdown"""
        return {
            "message": "Select a Drift preset from the dropdown",
            "message_type": "info",
            "options": self.get_preset_options(),
            "macros_html": ""  # Initialize with empty string to avoid showing placeholder
        }

    def handle_post(self, form):
        """Handle preset selection and editing"""
        action = form.getvalue('action')
        if action == 'select_preset' or action == 'edit_preset':
            preset_path = form.getvalue('preset_select')
            if not preset_path:
                return self.format_error_response("No preset selected")
            
            # If this is an edit action, update the preset with the new macro names
            if action == 'edit_preset':
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
            
            # Extract macro information from the selected preset (potentially updated)
            macro_result = extract_macro_information(preset_path)
            if not macro_result['success']:
                return self.format_error_response(macro_result['message'])
            
            # Generate HTML for displaying macros
            macros_html = self.generate_macros_html(macro_result['macros'])
            
            # Different message based on action
            if action == 'select_preset':
                message = f"Selected preset: {preset_path.split('/')[-1]}"
            else:  # edit_preset
                message = f"Saved preset: {preset_path.split('/')[-1]}"

            
            return {
                "message": message,
                "message_type": "success",
                "options": self.get_preset_options(),
                "macros_html": macros_html
            }
        
        return self.format_info_response("Unknown action")
        
    def generate_macros_html(self, macros):
        """Generate HTML for displaying macros"""
        if not macros:
            return "<p>No macros found in this preset.</p>"
        
        html = '<div class="macros-container">'
        
        for macro in macros:
            html += f'<div class="macro-item">'
            html += f'<div class="macro-header">'
            html += f'<span>Macro {macro["index"]}:</span> '
            html += f'<input type="text" name="macro_{macro["index"]}_name" value="{macro["name"]}" class="macro-name-input">'
            html += '</div>'
            
            if macro["parameters"]:
                html += '<ul class="parameters-list">'
                for param in macro["parameters"]:
                    param_info = f'{param["name"]}'
                    if "rangeMin" in param and "rangeMax" in param:
                        param_info += f' (Range: {param["rangeMin"]} - {param["rangeMax"]})'
                    html += f'<li>{param_info}</li>'
                html += '</ul>'
            else:
                html += '<p>No parameters mapped to this macro.</p>'
                
            html += '</div>'
            
        html += '</div>'
        return html
    
    def get_preset_options(self):
        """Get Drift preset options for the template dropdown"""
        try:
            result = scan_for_drift_presets()
            if not result['success']:
                return ''
            
            options_html = ['<option value="">--Select a Drift Preset--</option>']
            for preset in result['presets']:
                options_html.append(f'<option value="{preset["path"]}">{preset["name"]}</option>')
            return '\n'.join(options_html)
        except Exception as e:
            print(f"Error getting preset options: {e}")
            return ''
