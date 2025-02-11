#!/usr/bin/env python3
import os
import cgi
import shutil
from typing import Dict, Any, Optional, Tuple

class BaseHandler:
    """
    Base class for all feature handlers in the Move webserver.
    
    This class provides common functionality for handling web requests, including:
    - File upload handling with temporary storage
    - Form action validation
    - Response formatting
    - Cleanup of temporary files
    
    Each feature handler should inherit from this class and implement
    its own handle_post method to process specific feature requests.
    """
    
    def __init__(self):
        """
        Initialize the handler with a temporary uploads directory.
        Uses absolute path to prevent directory location issues.
        Creates the directory if it doesn't exist.
        """
        self.upload_dir = os.path.abspath("uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_action(self, form: cgi.FieldStorage, expected_action: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Validate that the form's action field matches the expected action.
        
        Args:
            form: The form data from the request
            expected_action: The action string that should be in the form
        
        Returns:
            tuple: (is_valid, error_response)
            - is_valid: True if action is valid, False otherwise
            - error_response: None if valid, error response dict if invalid
        """
        action = form.getvalue('action')
        if action != expected_action:
            return False, {"message": f"Bad Request: Invalid action '{action}'", "message_type": "error"}
        return True, None

    def handle_file_upload(self, form: cgi.FieldStorage, field_name: str = 'file') -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
        """
        Handle file upload from a multipart form.
        Saves the uploaded file to a temporary directory.
        
        Args:
            form: The form data from the request
            field_name: Name of the file field in the form (default: 'file')
        
        Returns:
            tuple: (success, filepath, error_response)
            - success: True if upload succeeded, False otherwise
            - filepath: Path to saved file if successful, None otherwise
            - error_response: Error response dict if failed, None if successful
        
        The caller is responsible for cleaning up the uploaded file
        by calling cleanup_upload() when the file is no longer needed.
        """
        if field_name not in form:
            return False, None, {"message": f"Bad Request: No {field_name} field in form", "message_type": "error"}

        file_field = form[field_name]
        if not isinstance(file_field, cgi.FieldStorage) or not file_field.filename:
            return False, None, {"message": f"Bad Request: Invalid {field_name}", "message_type": "error"}

        try:
            filename = os.path.basename(file_field.filename)
            filepath = os.path.join(self.upload_dir, filename)
            
            # Ensure upload directory exists
            os.makedirs(self.upload_dir, exist_ok=True)
            
            # Save the file
            with open(filepath, "wb") as f:
                shutil.copyfileobj(file_field.file, f)
            
            if not os.path.exists(filepath):
                return False, None, {"message": "File upload failed: File not saved", "message_type": "error"}
            
            return True, filepath, None
        except Exception as e:
            return False, None, {"message": f"Error saving uploaded file: {str(e)}", "message_type": "error"}

    def format_success_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Format a success response with optional additional data.
        
        Args:
            message: Success message to display
            **kwargs: Additional key-value pairs to include in response
        
        Returns:
            dict: Response dictionary with message and success type,
                 plus any additional provided data
        """
        response = {
            "message": message,
            "message_type": "success"
        }
        response.update(kwargs)
        return response

    def format_error_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Format an error response with optional additional data.
        
        Args:
            message: Error message to display
            **kwargs: Additional key-value pairs to include in response
        
        Returns:
            dict: Response dictionary with message and error type,
                 plus any additional provided data
        """
        response = {
            "message": message,
            "message_type": "error"
        }
        response.update(kwargs)
        return response

    def cleanup_upload(self, filepath: str):
        """
        Clean up an uploaded file.
        Should be called after processing is complete or if an error occurs.
        
        Args:
            filepath: Path to the file to remove
        
        Note:
            Silently ignores missing files and logs cleanup failures
            to avoid interrupting the response flow.
        """
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Warning: Failed to clean up uploaded file {filepath}: {e}")
