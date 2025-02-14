#!/usr/bin/env python3
import cgi
from handlers.base_handler import BaseHandler
from core.sample_editor_handler import get_wav_files



class SampleEditorHandler(BaseHandler):
    def get_wav_files(self):
        """Get WAV file options for the template."""
        wav_files = get_wav_files("/data/UserData/UserLibrary/Samples")

        return '<script> samples = [' + ''.join([f'"{file}",\n' for file in wav_files]) + '</script>'


    def handle_post(self, form: cgi.FieldStorage):
        """Handle POST request for your feature."""
        # Validate action
        valid, error_response = self.validate_action(form, "your_action")
        if not valid:
            return error_response

        try:
            # Extract parameters from form
            param1 = form.getvalue('param1')
            
            # Handle file upload if needed
            if 'file' in form:
                success, filepath, error_response = self.handle_file_upload(form)
                if not success:
                    return error_response
                
                # Process the file...
                # self.cleanup_upload(filepath)
            
            # Call core functionality
            result = sample_editor()
            
            if result['success']:
                return self.format_success_response(result['message'])
            else:
                return self.format_error_response(result['message'])
                
        except Exception as e:
            return self.format_error_response(f"Error processing request: {str(e)}")