#!/usr/bin/env python3
import os
import json
import cgi
from handlers.base_handler import BaseHandler
from core.chord_handler import process_kit, CHORDS

class ChordHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        # Create uploads directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)

    def handle_get(self):
        """
        Handle GET request for chord page.
        Returns chord information for the template.
        """
        # Return list of chords that will be generated
        return {
            'chords': [
                {'name': name, 'notes': notes}
                for name, notes in CHORDS.items()
            ]
        }

    def handle_post(self, form: cgi.FieldStorage, response_handler=None):
        """
        Handle POST request for chord processing.
        
        Args:
            form: The form data
            response_handler: Optional callable for sending responses directly
        """
        # Validate action
        valid, error_response = self.validate_action(form, "chord")
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

            # Process the kit
            result = process_kit(
                input_wav=filepath,
                preset_name=preset_name,
                mode=mode
            )

            if not result.get('success'):
                # Clean up only if processing failed
                self.cleanup_upload(filepath)
                return self.format_error_response(result.get('message', 'Kit processing failed'))

            if mode == "download":
                bundle_path = result.get('bundle_path')
                if os.path.exists(bundle_path):
                    try:
                        # Read bundle data
                        with open(bundle_path, "rb") as f:
                            bundle_data = f.read()

                        # Clean up uploaded file and uploads directory after reading bundle
                        self.cleanup_upload(filepath)
                        self.cleanup_directory(self.upload_dir)

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
                # For auto_place mode, clean up after successful processing
                self.cleanup_upload(filepath)
                self.cleanup_directory(self.upload_dir)
                return self.format_success_response(result.get('message', 'Kit processed successfully'))

        except Exception as e:
            # Clean up in case of any error
            self.cleanup_upload(filepath)
            self.cleanup_directory(self.upload_dir)
            return self.format_error_response(f"Error processing kit: {str(e)}")

    def cleanup_directory(self, directory):
        """Clean up a directory and its contents."""
        try:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    filepath = os.path.join(directory, filename)
                    try:
                        if os.path.isfile(filepath):
                            os.remove(filepath)
                        elif os.path.isdir(filepath):
                            self.cleanup_directory(filepath)
                            os.rmdir(filepath)
                    except Exception as e:
                        print(f"Warning: Failed to clean up {filepath}: {e}")
                if os.path.exists(directory):  # Check if directory still exists
                    try:
                        os.rmdir(directory)
                    except Exception as e:
                        print(f"Warning: Failed to remove directory {directory}: {e}")
        except Exception as e:
            print(f"Warning: Error cleaning directory {directory}: {e}")
