#!/usr/bin/env python3
"""Handler for the cyclic envelope visualizer."""

from handlers.base_handler import BaseHandler
from core.cyc_env_handler import get_cyc_env_defaults


class CycEnvHandler(BaseHandler):
    """Provide default values for the cyclic envelope page."""

    def handle_get(self):
        """Return default cyclic envelope settings."""
        return {
            "defaults": get_cyc_env_defaults(),
            "message": "Adjust parameters to shape the envelope",
            "message_type": "info",
        }
