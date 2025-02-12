#!/usr/bin/env python3
import cgi
from handlers.base_handler import BaseHandler
from core.drum_rack_inspector_handler import scan_for_drum_rack_presets, get_drum_cell_samples

class DrumRackInspectorHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request for drum rack inspector page."""
        return {
            'options': self.get_preset_options(),
            'message': '',
            'samples_html': ''
        }

    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for preset selection."""
        # Validate action
        valid, error_response = self.validate_action(form, "select_preset")
        if not valid:
            return error_response

        # Get preset path
        preset_path = form.getvalue('preset_select')
        if not preset_path:
            return self.format_error_response("No preset selected")

        try:
            result = get_drum_cell_samples(preset_path)
            if not result['success']:
                return self.format_error_response(result['message'])

            return {
                'options': self.get_preset_options(),
                'message': result['message'],
                'samples': result['samples']
            }

        except Exception as e:
            return self.format_error_response(f"Error processing preset: {str(e)}")

    def get_preset_options(self):
        """Get preset options for the template."""
        try:
            result = scan_for_drum_rack_presets()
            if not result['success']:
                return ''
            options_html = []
            for preset in result['presets']:
                options_html.append(f'<option value="{preset["path"]}">{preset["name"]}</option>')
            return '\n'.join(options_html)
        except Exception as e:
            print(f"Error getting preset options: {e}")
            return ''
