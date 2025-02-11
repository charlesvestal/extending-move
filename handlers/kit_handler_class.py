#!/usr/bin/env python3
import os
import json
import cgi
from base_handler import BaseHandler
from kit_handler import process_kit

class KitHandler(BaseHandler):
    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for kit processing."""
        # Validate action
        valid, error_response = self.validate_action(form, "slice")
        if not valid:
            return error_response

        # Validate mode
        mode = form.getvalue('mode')
        if not mode or mode not in ["download", "auto_place"]:
            return self.format_error_response("Bad Request: Invalid mode")

        # Handle file upload
        success, filepath, error_response = self.handle_file_upload(form)
        if not success:
            return error_response

        try:
            # Process form data
            preset_name = os.path.splitext(os.path.basename(filepath))[0]
            num_slices = int(form.getvalue('num_slices', 16))
            if not (1 <= num_slices <= 16):
                self.cleanup_upload(filepath)
                return self.format_error_response("Number of slices must be between 1 and 16")

            # Handle regions if provided
            regions = None
            if 'regions' in form:
                try:
                    regions = json.loads(form.getvalue('regions'))
                    num_slices = None
                except json.JSONDecodeError:
                    self.cleanup_upload(filepath)
                    return self.format_error_response("Invalid regions format")

            # Process the kit
            result = process_kit(
                input_wav=filepath,
                preset_name=preset_name,
                regions=regions,
                num_slices=num_slices,
                keep_files=False,
                mode=mode
            )

            # Clean up uploaded file
            self.cleanup_upload(filepath)

            if not result.get('success'):
                return self.format_error_response(result.get('message', 'Kit processing failed'))

            if mode == "download":
                return {
                    "success": True,
                    "download": True,
                    "bundle_path": result.get('bundle_path'),
                    "message": result.get('message', 'Kit processed successfully')
                }
            else:
                return self.format_success_response(result.get('message', 'Kit processed successfully'))

        except Exception as e:
            self.cleanup_upload(filepath)
            return self.format_error_response(f"Error processing kit: {str(e)}")
