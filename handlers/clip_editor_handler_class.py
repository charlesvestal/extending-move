#!/usr/bin/env python3
"""Handler for the Clip Editor prototype."""

from handlers.base_handler import BaseHandler
from core.clip_editor_handler import get_default_clip


class ClipEditorHandler(BaseHandler):
    """Provide clip data for the editor."""

    def handle_get(self):
        return get_default_clip()

    def handle_post(self, form):
        # Prototype does not yet support saving
        return self.format_error_response("Saving not implemented")

