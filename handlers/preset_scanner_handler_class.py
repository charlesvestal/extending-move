#!/usr/bin/env python3
import cgi
from handlers.base_handler import BaseHandler
from core.preset_scanner_handler import scan_for_drum_rack_presets

class PresetScannerHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request for preset scanner page."""
        return {
            'options': self.get_preset_options(),
            'message': ''
        }

    def get_preset_options(self):
        """Get preset options for the template."""
        try:
            result = scan_for_drum_rack_presets()
            if not result['success']:
                return ''
            return ''.join([f'<option value="{preset["path"]}">{preset["name"]}</option>' 
                          for preset in result['presets']])
        except Exception as e:
            print(f"Error getting preset options: {e}")
            return ''
