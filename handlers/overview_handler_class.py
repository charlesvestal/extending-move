#!/usr/bin/env python3
from handlers.base_handler import BaseHandler
from core.overview_handler import get_sets_data, get_active_slot, get_system_stats


class OverviewHandler(BaseHandler):
    def handle_get_data(self):
        """Return full sets data as JSON."""
        return get_sets_data()

    def handle_get_active_slot(self):
        """Return only the current active pad slot."""
        return {'current_slot': get_active_slot()}

    def handle_get_system_stats(self):
        """Return CPU load and memory usage."""
        return get_system_stats()
