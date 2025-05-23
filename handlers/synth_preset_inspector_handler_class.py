#!/usr/bin/env python3
import re
import os
from handlers.base_handler import BaseHandler
from core.synth_preset_inspector_handler import get_synth_presets, get_synth_preset_details

class SynthPresetInspectorHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request to show synth preset inspector."""
        try:
            # Get list of synth presets
            presets_result = get_synth_presets()
            if presets_result.get('success'):
                return {
                    "success": True,
                    "presets": presets_result.get('presets', [])
                }
            else:
                return {
                    "success": False,
                    "message": presets_result.get('message', 'Failed to load synth presets'),
                    "message_type": "error"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error loading synth presets: {str(e)}",
                "message_type": "error"
            }

    def handle_post(self, form):
        """Handle POST request for synth preset inspection."""
        # Get action from form
        action = form.getvalue('action') if hasattr(form, 'getvalue') else form.get('action')
        
        if action == "inspect_preset":
            preset_path = form.getvalue('preset_path') if hasattr(form, 'getvalue') else form.get('preset_path')
            if not preset_path:
                return self.format_error_response("Please select a preset to inspect")
            
            try:
                # Get synth preset details
                details_result = get_synth_preset_details(preset_path)
                if details_result.get('success'):
                    return self.format_success_response(
                        "Preset loaded successfully",
                        details=details_result.get('details', {})
                    )
                else:
                    return self.format_error_response(details_result.get('message', 'Failed to inspect preset'))
            except Exception as e:
                return self.format_error_response(f"Error inspecting preset: {str(e)}")
        
        else:
            return self.format_error_response("Invalid action")
