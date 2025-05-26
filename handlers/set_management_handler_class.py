

from handlers.base_handler import BaseHandler
from core.set_management_handler import create_set

class SetManagementHandler(BaseHandler):
    def handle_get(self):
        """
        Return empty context for rendering the Set Management page.
        """
        return {}

    def handle_post(self, form):
        """
        Handle POST request to create a new set file.
        """
        set_name = form.getvalue('set_name')
        if not set_name:
            return self.format_error_response("Missing required parameter: set_name")
        result = create_set(set_name)
        if result['success']:
            return self.format_success_response(result['message'])
        else:
            return self.format_error_response(result['message'])