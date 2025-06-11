#!/usr/bin/env python3
"""Handler for the LFO visualizer."""

from handlers.base_handler import BaseHandler
from core.lfo_visualizer import get_lfo_defaults


class LFOHandler(BaseHandler):
    """Provide default values for the LFO page."""

    def handle_get(self):
        return {
            "defaults": get_lfo_defaults(),
            "message": "Adjust parameters to shape the LFO",
            "message_type": "info",
        }
