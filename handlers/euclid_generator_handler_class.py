from handlers.base_handler import BaseHandler
from core.euclid_generator_handler import create_euclid_clip


class EuclidGeneratorHandler(BaseHandler):
    """Handle Euclidean clip generation requests."""

    def handle_get(self):
        return {
            "message": "Fill parameters and generate",
            "message_type": "info",
            "set_path": "",
            "track_index": 0,
            "clip_index": 0,
            "copy_track_index": 0,
        }

    def handle_post(self, form):
        set_path = form.getvalue("set_path")
        track_index = int(form.getvalue("track_index", 0))
        clip_index = int(form.getvalue("clip_index", 0))
        ref_track = form.getvalue("copy_track_index")
        reference_track = int(ref_track) if ref_track is not None else None
        pulses = [int(form.getvalue(f"pulses_{i}", 0)) for i in range(16)]
        rotates = [int(form.getvalue(f"rotate_{i}", 0)) for i in range(16)]
        result = create_euclid_clip(
            set_path,
            track_index,
            clip_index,
            pulses,
            rotates,
            reference_track,
        )
        result.update({
            "set_path": set_path,
            "track_index": track_index,
            "clip_index": clip_index,
            "copy_track_index": reference_track or 0,
        })
        return result
