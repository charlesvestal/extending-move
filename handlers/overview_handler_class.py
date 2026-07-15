#!/usr/bin/env python3
import os
import logging
from handlers.base_handler import BaseHandler
from core.overview_handler import get_sets_data, get_active_slot, get_system_stats
from core.restore_handler import restore_ablbundle, restore_abl
from core.pad_colors import PAD_COLORS, PAD_COLOR_LABELS
import json


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

    def handle_post_restore(self, form):
        """Handle restore POST request from Overview page."""
        try:
            # Validate file upload
            success, filepath, error_response = self.handle_file_upload(form, "ablbundle")
            if not success:
                return {"success": False, "message": error_response.get('message', "Failed to upload file") if error_response else "Upload failed"}

            # Get form values
            pad_selected = form.getvalue("target_pad")
            pad_color = form.getvalue("pad_color")

            # Validate pad selection
            if not pad_selected or not pad_selected.isdigit():
                self.cleanup_upload(filepath)
                return {"success": False, "message": "Please select a target pad from the grid."}

            # Validate color
            if not pad_color or not pad_color.isdigit():
                self.cleanup_upload(filepath)
                return {"success": False, "message": "Please select a pad color."}

            pad_selected = int(pad_selected) - 1  # Convert to internal ID (0-31)
            pad_color = int(pad_color)

            # Execute restore
            if filepath.lower().endswith('.ablbundle'):
                result = restore_ablbundle(filepath, pad_selected, pad_color)
            else:
                result = restore_abl(filepath, pad_selected, pad_color)

            self.cleanup_upload(filepath)
            if result.get("success"):
                result["message"] = result["message"].replace(
                    f"pad {pad_selected}", f"pad {pad_selected + 1}"
                )
            return result

        except Exception as e:
            logging.error(f"Error in handle_post_restore: {str(e)}")
            return {"success": False, "message": f"Error restoring set: {str(e)}"}

    def generate_color_options_json(self):
        """Return pad colors and labels as JSON for client-side use."""
        colors = [PAD_COLORS[i] for i in sorted(PAD_COLORS)]
        names = [PAD_COLOR_LABELS[i] for i in sorted(PAD_COLOR_LABELS)]
        return {"colors": colors, "names": names}
