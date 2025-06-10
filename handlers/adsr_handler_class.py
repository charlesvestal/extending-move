#!/usr/bin/env python3
"""Handler for the ADSR envelope visualizer prototype."""

from handlers.base_handler import BaseHandler
from core.adsr_handler import get_adsr_defaults


class AdsrHandler(BaseHandler):
    """Provide default values for the ADSR visualizer."""

    def handle_get(self):
        """Return default ADSR settings."""
        return {
            "defaults": get_adsr_defaults(),
            "message": "Adjust the knobs to shape the envelope",
            "message_type": "info",
        }
