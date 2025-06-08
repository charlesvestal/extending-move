#!/usr/bin/env python3
"""Web handler for the update feature."""
from handlers.base_handler import BaseHandler
from core.update_handler import check_update_available, perform_update


class UpdateHandler(BaseHandler):
    """Handle update checks and application."""

    def handle_get(self):
        available, message = check_update_available()
        return {
            "message": message,
            "message_type": "info",
            "update_available": available,
        }

    def handle_post(self, form):
        valid, error = self.validate_action(form, "perform_update")
        if not valid:
            return error
        success, message = perform_update()
        msg_type = "success" if success else "error"
        return {
            "message": message,
            "message_type": msg_type,
            "update_available": False,
        }
