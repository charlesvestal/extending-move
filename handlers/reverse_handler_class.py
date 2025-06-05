#!/usr/bin/env python3
import cgi
import os
from handlers.base_handler import BaseHandler
from core.reverse_handler import get_wav_files, reverse_wav_file
from core.file_browser import build_file_browser_html

class ReverseHandler(BaseHandler):
    def handle_get(self):
        """Provide the file browser HTML for reverse page."""
        base_dir = "/data/UserData/UserLibrary/Samples"
        wav_files = get_wav_files(base_dir)
        file_paths = [os.path.join(base_dir, f) for f in wav_files]
        browser_html = build_file_browser_html(
            file_paths, base_dir, "/reverse", "wav_file", "reverse_file"
        )
        return {
            "file_browser_html": browser_html,
            "message": "Select a WAV file to reverse",
            "message_type": "info",
            "selected_file": None,
        }

    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for WAV file reversal."""
        # Validate action
        valid, error_response = self.validate_action(form, "reverse_file")
        if not valid:
            return error_response

        # Get WAV file selection
        wav_file = form.getvalue('wav_file')
        if not wav_file:
            return self.format_error_response("Bad Request: No WAV file selected")

        try:
            success, message, new_path = reverse_wav_file(
                filename=wav_file,
                directory="/data/UserData/UserLibrary/Samples",
            )
            if success and new_path and new_path != wav_file:
                message = f"{message}\nNew file path: {new_path}"
            msg_type = "success" if success else "error"
            return {
                "message": message,
                "message_type": msg_type,
                "selected_file": wav_file,
                "file_browser_html": None,
            }
        except Exception as e:
            return self.format_error_response(f"Error processing reverse WAV file: {str(e)}")

    def get_wav_options(self):
        """Deprecated: dropdown options no longer used."""
        return ""
