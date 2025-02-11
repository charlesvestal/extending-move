#!/usr/bin/env python3
import cgi
from base_handler import BaseHandler
from reverse_handler import get_wav_files, reverse_wav_file

class ReverseHandler(BaseHandler):
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
            success, message = reverse_wav_file(
                filename=wav_file,
                directory="/data/UserData/UserLibrary/Samples"
            )
            if success:
                return self.format_success_response(message)
            else:
                return self.format_error_response(message)
        except Exception as e:
            return self.format_error_response(f"Error processing reverse WAV file: {str(e)}")

    def get_wav_options(self):
        """Get WAV file options for the template."""
        return get_wav_files("/data/UserData/UserLibrary/Samples")
