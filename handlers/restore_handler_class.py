#!/usr/bin/env python3
import logging
from handlers.base_handler import BaseHandler
from core.restore_handler import restore_bundle
from core.list_msets_handler import list_msets

class RestoreHandler(BaseHandler):
    def handle_get(self):
        """Handle GET request to show restore form with Move Set options."""
        try:
            # Get list of Move Sets
            msets_result = list_msets()
            if msets_result.get('success'):
                options_html = msets_result.get('options_html', '')
                return {
                    "success": True,
                    "options": options_html
                }
            else:
                return {
                    "success": False,
                    "message": msets_result.get('message', 'Failed to load Move Sets'),
                    "message_type": "error"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error loading Move Sets: {str(e)}",
                "message_type": "error"
            }

    def handle_post(self, form):
        """Handle POST request for bundle restoration."""
        # Validate action
        valid, error_response = self.validate_action(form, "restore")
        if not valid:
            return error_response

        # Get form values
        mset_index = form.getvalue('mset_index') if hasattr(form, 'getvalue') else form.get('mset_index')
        mset_restorecolor = form.getvalue('mset_restorecolor') if hasattr(form, 'getvalue') else form.get('mset_restorecolor')

        if not mset_index:
            return self.format_error_response("Please select a Move Set slot")

        if mset_restorecolor is None:
            return self.format_error_response("Please select a color")

        # Handle file upload
        success, filepath, error_response = self.handle_file_upload(form)
        if not success:
            return error_response

        try:
            # Process the bundle restoration
            result = restore_bundle(
                bundle_path=filepath,
                mset_index=int(mset_index),
                mset_restorecolor=int(mset_restorecolor)
            )
            
            # Clean up uploaded file
            self.cleanup_upload(filepath)
            
            if result.get('success'):
                return self.format_success_response(result.get('message', 'Bundle restored successfully'))
            else:
                return self.format_error_response(result.get('message', 'Failed to restore bundle'))
                
        except Exception as e:
            # Clean up in case of error
            self.cleanup_upload(filepath)
            return self.format_error_response(f"Error restoring bundle: {str(e)}")
