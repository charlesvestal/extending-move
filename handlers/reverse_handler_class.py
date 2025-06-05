#!/usr/bin/env python3
import cgi
from handlers.base_handler import BaseHandler
from core.reverse_handler import reverse_wav_file
from core.file_browser import list_directory

class ReverseHandler(BaseHandler):
    def handle_get(self):
        """Return informational message for the reverse page."""
        return {
            "message": "Select a WAV file to reverse",
            "message_type": "info",
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
                directory="/data/UserData/UserLibrary/Samples"
            )
            if not success:
                return self.format_error_response(message)
                
            # Include the new path in the success message if it's different from the original
            if new_path and new_path != wav_file:
                message = f"{message}\nNew file path: {new_path}"
            return self.format_success_response(message)
        except Exception as e:
            return self.format_error_response(f"Error processing reverse WAV file: {str(e)}")


    def list_directory(self, rel_path: str):
        """Return directories and WAV files for a given relative path."""
        return list_directory(
            "/data/UserData/UserLibrary/Samples",
            rel_path,
            [".wav", ".aif", ".aiff"],
        )

