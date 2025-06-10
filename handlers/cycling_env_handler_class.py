#!/usr/bin/env python3
"""Handler for the Cycling Envelope visualizer prototype."""

from handlers.base_handler import BaseHandler
from core.cycling_env_handler import get_cycling_env_defaults


class CyclingEnvHandler(BaseHandler):
    """Provide default values for the Cycling Envelope visualizer."""

    def handle_get(self):
        """Return default Cycling Envelope settings."""
        return {
            "defaults": get_cycling_env_defaults(),
            "message": "Adjust parameters to shape the cycling envelope",
            "message_type": "info",
        }
