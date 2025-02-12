#!/usr/bin/env python3
import cgi
from handlers.base_handler import BaseHandler
from core.preset_scanner_handler import scan_for_drum_rack_presets

class PresetScannerHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request to populate the preset dropdown."""
        try:
            result = scan_for_drum_rack_presets()
            
            if not result['success']:
                return self.format_error_response(result['message'])
            
            # Generate HTML options for the dropdown
            options_html = ""
            for preset in result['presets']:
                options_html += f'<option value="{preset["path"]}">{preset["name"]}</option>\n'
            
            return {
                'options': options_html,
                'message': result['message']
            }
            
        except Exception as e:
            return self.format_error_response(f"Error handling request: {str(e)}")
