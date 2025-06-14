from handlers.base_handler import BaseHandler
import json
from core.pad_pitch_handler import extract_pad_clip, save_pad_clip


class PadPitchHandler(BaseHandler):
    def handle_get(self, form):
        set_path = form.getvalue("set_path")
        track = form.getvalue("track_index")
        clip = form.getvalue("clip_index")
        pad = form.getvalue("pad_number")
        if not (set_path and track and clip and pad):
            return self.format_error_response("Missing parameters")
        try:
            data = extract_pad_clip(set_path, int(track), int(clip), int(pad))
            data.update({
                "selected_set": set_path,
                "track_index": int(track),
                "clip_index": int(clip),
                "pad_number": int(pad),
                "message": "Pad clip loaded",
                "message_type": "success",
            })
            return data
        except Exception as e:
            return self.format_error_response(f"Failed to load pad clip: {e}")

    def handle_post(self, form):
        set_path = form.getvalue("set_path")
        track = form.getvalue("track_index")
        clip = form.getvalue("clip_index")
        pad = form.getvalue("pad_number")
        notes_data = form.getvalue("clip_notes")
        region_end = form.getvalue("region_end")
        loop_start = form.getvalue("loop_start")
        loop_end = form.getvalue("loop_end")
        if not all([set_path, track, clip, pad, notes_data, region_end, loop_start, loop_end]):
            return self.format_error_response("Missing parameters")
        try:
            notes = json.loads(notes_data)
            region_end = float(region_end)
            loop_start = float(loop_start)
            loop_end = float(loop_end)
        except Exception:
            return self.format_error_response("Invalid data")
        result = save_pad_clip(set_path, int(track), int(clip), int(pad), notes, region_end, loop_start, loop_end)
        if not result.get("success"):
            return self.format_error_response(result.get("message"))
        return {
            "message": result.get("message"),
            "message_type": "success",
            **extract_pad_clip(set_path, int(track), int(clip), int(pad)),
            "selected_set": set_path,
            "track_index": int(track),
            "clip_index": int(clip),
            "pad_number": int(pad),
        }
