#!/usr/bin/env python3
import cgi
from base_handler import BaseHandler
from refresh_handler import refresh_library

class RefreshHandler(BaseHandler):
    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for library refresh."""
        # Validate action
        valid, error_response = self.validate_action(form, "refresh_library")
        if not valid:
            return error_response

        try:
            success, message = refresh_library()
            if success:
                return self.format_success_response(message)
            else:
                return self.format_error_response(message)
        except Exception as e:
            return self.format_error_response(f"Error refreshing library: {str(e)}")
