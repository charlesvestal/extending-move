#!/usr/bin/env python3
import cgi
import os
from handlers.base_handler import BaseHandler
from core.reverse_handler import reverse_wav_file

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
        base_dir = "/data/UserData/UserLibrary/Samples"
        abs_dir = os.path.realpath(os.path.join(base_dir, rel_path))
        base_real = os.path.realpath(base_dir)
        if not abs_dir.startswith(base_real):
            return {"success": False, "message": "Invalid path"}
        if not os.path.isdir(abs_dir):
            return {"success": False, "message": "Not a directory"}

        dirs = []
        files = []
        for entry in sorted(os.listdir(abs_dir)):
            if entry.startswith('.'):
                continue
            full = os.path.join(abs_dir, entry)
            if os.path.isdir(full):
                dirs.append(entry)
            elif entry.lower().endswith((".wav", ".aif", ".aiff")):
                files.append(entry)
        return {"success": True, "dirs": dirs, "files": files, "path": rel_path}

