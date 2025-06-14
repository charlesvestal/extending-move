#!/usr/bin/env python3
"""Handler for viewing drum pad pitchbend notes."""

import json
from handlers.base_handler import BaseHandler
from core.pitchbend_editor_handler import get_pad_notes


class PitchbendEditorHandler(BaseHandler):
    """Simple handler exposing pitchbend note information."""

    def handle_get(self):
        return {
            "notes": None,
            "message": "Paste note JSON and select pad",
            "message_type": "info",
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        if action != "display":
            return self.format_error_response("Invalid action")
        notes_json = form.getvalue("notes_data")
        pad_number = form.getvalue("pad_number")
        if notes_json is None or pad_number is None:
            return self.format_error_response("Missing notes or pad number")
        try:
            notes = json.loads(notes_json)
            pad = int(pad_number)
        except Exception as exc:  # noqa: BLE001
            return self.format_error_response(f"Error parsing input: {exc}")
        pad_notes = get_pad_notes(notes, pad)
        return self.format_success_response("Parsed notes", notes=pad_notes)
