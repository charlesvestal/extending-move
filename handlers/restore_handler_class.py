import os
import cgi
import logging
from handlers.base_handler import BaseHandler
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle

class RestoreHandler(BaseHandler):
    """
    Handles web requests for set restore.
    """

    def handle_get(self):
        """
        Handles GET requests to display available pads for restoration.

        Returns:
            dict: Context for rendering the restore.html template.
        """
        try:
            _, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])  # Use .get() to avoid KeyError
            logging.info(f"Available Pads: {free_pads}")
            
            return {
                "options": self.generate_pad_options(free_pads),
                "message": f"Available pads: {', '.join(map(str, free_pads))}" if free_pads else "No pads available."
            }
        
        except Exception as e:
            logging.error(f"Error retrieving free pads: {str(e)}")
            return {
                "options": '<option value="" disabled>Error loading pads</option>',
                "message": "Error retrieving available pads."
            }

    def handle_post(self, form: cgi.FieldStorage):
        """
        Handles POST requests to restore an uploaded .ablbundle file.
        
        Args:
            form (cgi.FieldStorage): Form data from the request.
        
        Returns:
            dict: Response message indicating success or failure.
        """
        valid, error_response = self.validate_action(form, "restore_ablbundle")
        if not valid:
            return error_response

        pad_selected = form.getvalue("mset_index")
        pad_color = form.getvalue("mset_color")

        if not pad_selected or not pad_selected.isdigit():
            return self.format_error_response("Invalid pad selection provided.")
        if not pad_color or not pad_color.isdigit():
            return self.format_error_response("Invalid pad color provided.")

        pad_selected = int(pad_selected) - 1  # Convert back to internal ID
        pad_color = int(pad_color)

        if not (0 <= pad_selected <= 31):
            return self.format_error_response("Invalid pad selection. Must be between 1 and 32.")
        if not (1 <= pad_color <= 26):
            return self.format_error_response("Invalid pad color. Must be between 1 and 26.")

        success, filepath, error_response = self.handle_file_upload(form, "ablbundle")
        if not success:
            return error_response

        try:
            result = restore_ablbundle(filepath, pad_selected, pad_color)
            self.cleanup_upload(filepath)
            if result["success"]:
                _, ids = list_msets(return_free_ids=True)
                free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
                options = self.generate_pad_options(free_pads)
                return self.format_success_response(result["message"], options)
            else:
                return self.format_error_response(result["message"])
        except Exception as e:
            return self.format_error_response(f"Error restoring bundle: {str(e)}")

    def generate_pad_options(self, free_pads):
        """
        Generates HTML <option> elements for available pads.
        
        Args:
            free_pads (list): List of available pad numbers.
        
        Returns:
            str: HTML-formatted options for a dropdown.
        """
        if not free_pads:
            return '<option value="" disabled>No pads available</option>'
        options = [f'<option value="{pad}" {"selected" if pad == free_pads[0] else ""}>{pad}</option>' for pad in free_pads]
        return ''.join(options)

    def format_success_response(self, message, options):
        return {
            "message": f"<p style='color: green;'>{message}</p>",
            "options": options
        }
