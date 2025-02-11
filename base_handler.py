#!/usr/bin/env python3
import os
import cgi
import shutil
from typing import Dict, Any, Optional, Tuple

class BaseHandler:
    """Base class for all feature handlers."""
    
    def __init__(self):
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_action(self, form: cgi.FieldStorage, expected_action: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Validate the action field in the form."""
        action = form.getvalue('action')
        if action != expected_action:
            return False, {"message": f"Bad Request: Invalid action '{action}'", "message_type": "error"}
        return True, None

    def handle_file_upload(self, form: cgi.FieldStorage, field_name: str = 'file') -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
        """
        Handle file upload from form.
        Returns: (success, filepath, error_response)
        """
        if field_name not in form:
            return False, None, {"message": f"Bad Request: No {field_name} field in form", "message_type": "error"}

        file_field = form[field_name]
        if not isinstance(file_field, cgi.FieldStorage) or not file_field.filename:
            return False, None, {"message": f"Bad Request: Invalid {field_name}", "message_type": "error"}

        try:
            filename = os.path.basename(file_field.filename)
            filepath = os.path.join(self.upload_dir, filename)
            
            with open(filepath, "wb") as f:
                shutil.copyfileobj(file_field.file, f)
            
            return True, filepath, None
        except Exception as e:
            return False, None, {"message": f"Error saving uploaded file: {str(e)}", "message_type": "error"}

    def format_success_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """Format a success response with optional additional data."""
        response = {
            "message": message,
            "message_type": "success"
        }
        response.update(kwargs)
        return response

    def format_error_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """Format an error response with optional additional data."""
        response = {
            "message": message,
            "message_type": "error"
        }
        response.update(kwargs)
        return response

    def cleanup_upload(self, filepath: str):
        """Clean up uploaded file."""
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Warning: Failed to clean up uploaded file {filepath}: {e}")
