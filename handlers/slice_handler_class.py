#!/usr/bin/env python3
import os
import json
import logging
from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)
from core.slice_handler import process_kit

class SliceHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        # Create uploads directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)

    def handle_detect_transients(self, form):
        import json
        from core.slice_handler import detect_transients

        # Accept file upload from form as 'file'
        if 'file' not in form:
            return self.format_json_response({'success': False, 'message': 'No file provided.'}, status=400)
        success, filepath, error_response = self.handle_file_upload(form)
        if not success:
            return self.format_json_response({'success': False, 'message': 'File upload failed.'}, status=400)
        try:
            # --- Sensitivity support ---
            delta = 0.07  # default
            if "sensitivity" in form:
                try:
                    delta = float(form.getvalue("sensitivity"))
                except Exception:
                    pass
            # Detect all transients to determine total count
            all_regions = detect_transients(filepath, max_slices=None, delta=delta)
            total_detected = len(all_regions) if all_regions else 0
            # Use only the first 16 regions for mapping
            regions = all_regions[:16] if all_regions else []
            if total_detected > 16:
                message = f"Detected {total_detected} transients. Mapping the first 16."
            elif total_detected > 0:
                message = f"Detected {total_detected} transients."
            else:
                message = "No transients detected. Using full file."
            if regions and len(regions) > 0:
                resp = {'success': True, 'regions': regions, 'message': message}
            else:
                resp = {'success': False, 'regions': [{'start': 0.0, 'end': 1.0}], 'message': message}
            return self.format_json_response(resp)
        except Exception as e:
            return self.format_json_response({'success': False, 'message': str(e)}, status=500)
        finally:
            self.cleanup_upload(filepath)


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
                        logger.warning("Failed to clean up %s: %s", filepath, e)
                if os.path.exists(directory):  # Check if directory still exists
                    try:
                        os.rmdir(directory)
                    except Exception as e:
                        logger.warning("Failed to remove directory %s: %s", directory, e)
        except Exception as e:
            logger.warning("Error cleaning directory %s: %s", directory, e)

    def handle_post(self, form, response_handler=None):
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

        # Get kit type from form
        kit_type = form.getvalue('kit_type', 'choke')

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

            # Detect transient mode
            transient_detect = form.getvalue('transient_detect') in ['1', 'true', 'True', 'on']

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
                mode=mode,
                kit_type=kit_type,
                transient_detect=transient_detect
            )

            if not result.get('success'):
                # Clean up only if processing failed
                self.cleanup_upload(filepath)
                message = result.get('message', 'Kit processing failed')
                if not isinstance(message, str):
                    message = str(message)
                return self.format_error_response(message)

            # --- BEGIN: Inject detected regions into HTML if transient_detect and regions ---
            # This block is only relevant for rendering HTML responses (not downloads)
            # so we insert a <script> tag at the end of the HTML output if needed.
            if mode != "download" and transient_detect:
                # Prepare detected regions for script injection
                detected_regions = None
                # If the result contains detected regions, use them
                if transient_detect and result.get('regions'):
                    detected_regions = result['regions']
                # If not, fallback to regions variable if available
                elif transient_detect and regions:
                    detected_regions = regions

                html_output = self.format_success_response(result.get('message', 'Kit processed successfully'))
                if isinstance(html_output, dict) and 'html' in html_output:
                    html = html_output['html']
                else:
                    html = str(html_output)

                # Compose the transient message to prepend to html
                if detected_regions and len(detected_regions) > 1:
                    transient_msg = f"<div style='color: green;'>Detected {len(detected_regions)} transients; regions set automatically.</div>"
                else:
                    transient_msg = "<div style='color: orange;'>No transients detected; using the whole file as one region.</div>"
                html = transient_msg + html

                # If there are detected regions, append the <script> tag as before
                if detected_regions:
                    html += f"""
        <script>
        window.DETECTED_REGIONS = {json.dumps(detected_regions)};
        </script>
        """
                # Always append a console log about transient detection
                html += f"<script>console.log('Transient detection attempted: {len(detected_regions) if detected_regions else 0} regions detected.');</script>"
                return {'message_html': html}
            # --- END: Inject detected regions into HTML if transient_detect and regions ---

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
                    message = "Bundle file not found"
                    if not isinstance(message, str):
                        message = str(message)
                    return self.format_error_response(message)
            else:
                # For auto_place mode, clean up after successful processing
                self.cleanup_upload(filepath)
                self.cleanup_directory(self.upload_dir)
                message = result.get('message', 'Kit processed successfully')
                if not isinstance(message, str):
                    message = str(message)
                return self.format_success_response(message)

        except Exception as e:
            # Clean up in case of any error
            self.cleanup_upload(filepath)
            self.cleanup_directory(self.upload_dir)
            return self.format_error_response(f"Error processing kit in class: {str(e)}")
