from handlers.base_handler import BaseHandler
from core.update_handler import check_for_update, perform_update


class UpdateHandler(BaseHandler):
    """Handler for checking and applying repository updates."""

    def handle_get(self):
        update_available, commits = check_for_update()
        return {
            "update_available": update_available,
            "commits": commits,
        }

    def handle_post(self, form):
        valid, error_response = self.validate_action(form, "do_update")
        if not valid:
            return error_response
        progress = []
        success = perform_update(progress.append)
        message = "Update complete" if success else "Update failed"
        return {
            "message": message,
            "message_type": "success" if success else "error",
            "progress": progress,
            "update_available": False,
        }
