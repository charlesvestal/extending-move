#!/usr/bin/env python3
import json
from handlers.base_handler import BaseHandler
from core.reverse_handler import reverse_wav

class ReverseHandler(BaseHandler):
    def handle_post(self, form):
        """Handle POST request for WAV reversal."""
        # Validate action
        valid, error_response = self.validate_action(form, "reverse")
        if not valid:
            return error_response

        # Handle file upload
        success, filepath, error_response = self.handle_file_upload(form)
        if not success:
            return error_response

        try:
            # Process the WAV file
            result = reverse_wav(filepath)
            
            # Clean up uploaded file
            self.cleanup_upload(filepath)
            
            if result.get('success'):
                return self.format_success_response(result.get('message', 'WAV file reversed successfully'))
            else:
                return self.format_error_response(result.get('message', 'Failed to reverse WAV file'))
                
        except Exception as e:
            # Clean up in case of error
            self.cleanup_upload(filepath)
            return self.format_error_response(f"Error processing WAV file: {str(e)}")
