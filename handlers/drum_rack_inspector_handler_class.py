#!/usr/bin/env python3
import os
from handlers.base_handler import BaseHandler
from core.drum_rack_inspector_handler import scan_for_drum_rack_presets, get_drum_cell_samples

class DrumRackInspectorHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request to show drum rack inspector."""
        try:
            # Get list of drum rack presets
            presets_result = scan_for_drum_rack_presets()
            if presets_result.get('success'):
                return {
                    "success": True,
                    "presets": presets_result.get('presets', [])
                }
            else:
                return {
                    "success": False,
                    "message": presets_result.get('message', 'Failed to load drum rack presets'),
                    "message_type": "error"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error loading drum rack presets: {str(e)}",
                "message_type": "error"
            }

    def handle_post(self, form):
        """Handle POST request for drum rack inspection."""
        # Get action from form
        action = form.getvalue('action') if hasattr(form, 'getvalue') else form.get('action')
        
        if action == "inspect_preset":
            preset_path = form.getvalue('preset_path') if hasattr(form, 'getvalue') else form.get('preset_path')
            if not preset_path:
                return self.format_error_response("Please select a preset to inspect")
            
            try:
                # Get drum rack details
                details_result = get_drum_cell_samples(preset_path)
                if details_result.get('success'):
                    return self.format_success_response(
                        "Preset loaded successfully",
                        samples=details_result.get('samples', [])
                    )
                else:
                    return self.format_error_response(details_result.get('message', 'Failed to inspect preset'))
            except Exception as e:
                return self.format_error_response(f"Error inspecting preset: {str(e)}")
        
        else:
            return self.format_error_response("Invalid action")
