#!/usr/bin/env python3
import os
import json
import cgi
from base_handler import BaseHandler
from slice_handler import process_kit

class SliceHandler(BaseHandler):
    def handle_post(self, form: cgi.FieldStorage, response_handler=None):
        """
        Handle POST request for slice processing.
        
        Args:
            form: The form data
            response_handler: A callable that takes (status, headers, content) for sending responses
        """
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
                bundle_path = result.get('bundle_path')
                if os.path.exists(bundle_path):
                    try:
                        # Read bundle data
                        with open(bundle_path, "rb") as f:
                            bundle_data = f.read()

                        # If response_handler is provided, use it to send the response
                        if response_handler:
                            headers = [
                                ("Content-Type", "application/zip"),
                                ("Content-Disposition", f"attachment; filename={os.path.basename(bundle_path)}"),
                                ("Content-Length", str(len(bundle_data)))
                            ]
                            response_handler(200, headers, bundle_data)
                            os.remove(bundle_path)
                            return None

                        # Otherwise return the bundle data for the server to handle
                        return {
                            "success": True,
                            "download": True,
                            "bundle_path": bundle_path,
                            "message": result.get('message', 'Kit processed successfully')
                        }
                    except Exception as e:
                        if os.path.exists(bundle_path):
                            os.remove(bundle_path)
                        return self.format_error_response(f"Error reading bundle: {str(e)}")
                else:
                    return self.format_error_response("Bundle file not found")
            else:
                return self.format_success_response(result.get('message', 'Kit processed successfully'))

        except Exception as e:
            self.cleanup_upload(filepath)
            return self.format_error_response(f"Error processing kit: {str(e)}")
