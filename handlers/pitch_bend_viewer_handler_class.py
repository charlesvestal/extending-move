from handlers.base_handler import BaseHandler
from core.pitch_bend_handler import get_pad_pitch_data

class PitchBendViewerHandler(BaseHandler):
    def handle_get(self):
        return {
            "message": "Select a set and clip to view pitch bends",
            "segments": [],
            "set_path": "",
            "track_idx": 0,
            "clip_idx": 0,
            "pad_note": 36,
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        set_path = form.getvalue("set_path")
        track_idx = int(form.getvalue("track_idx") or 0)
        clip_idx = int(form.getvalue("clip_idx") or 0)
        pad_note = int(form.getvalue("pad_note") or 36)

        if action == "load":
            if not set_path:
                return self.format_error_response("Set path required")
            result = get_pad_pitch_data(set_path, track_idx, clip_idx, pad_note)
            if not result.get("success"):
                return self.format_error_response(result.get("message"))
            return {
                "message": result.get("message"),
                "segments": result.get("segments"),
                "set_path": set_path,
                "track_idx": track_idx,
                "clip_idx": clip_idx,
                "pad_note": pad_note,
            }
        return self.format_error_response("Unknown action")
