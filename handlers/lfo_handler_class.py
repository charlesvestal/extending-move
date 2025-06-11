#!/usr/bin/env python3
"""Handler for the LFO cycle visualizer."""

from handlers.base_handler import BaseHandler
from core.lfo_handler import get_lfo_defaults


class LfoHandler(BaseHandler):
    """Provide default values for the LFO visualizer."""

    def handle_get(self):
        """Return default LFO settings."""
        return {
            "defaults": get_lfo_defaults(),
            "message": "Adjust parameters to shape the LFO",
            "message_type": "info",
        }
