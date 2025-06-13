from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.set_inspector_handler import list_clips, get_clip_data
import os

class SetInspectorHandler(BaseHandler):
    def handle_get(self):
        base_dir = "/data/UserData/UserLibrary/Sets"
        if not os.path.exists(base_dir) and os.path.exists("examples/Sets"):
            base_dir = "examples/Sets"
        browser_html = generate_dir_html(
            base_dir,
            "",
            "/set-inspector",
            "set_path",
            "select_set",
        )
        return {
            "file_browser_html": browser_html,
            "message": "Select a set to inspect",
            "message_type": "info",
            "selected_set": None,
            "clip_options": "",
            "selected_clip": None,
            "notes": [],
            "envelopes": [],
            "region": 4.0,
            "browser_root": base_dir,
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        if action == "select_set":
            set_path = form.getvalue("set_path")
            if not set_path:
                return self.format_error_response("No set selected")
            result = list_clips(set_path)
            if not result.get("success"):
                return self.format_error_response(result.get("message"))
            options = "".join(
                f'<option value="{c["track"]}:{c["clip"]}">{c["name"]}</option>'
                for c in result.get("clips", [])
            )
            options = '<option value="" disabled selected>-- Select Clip --</option>' + options
            base_dir = "/data/UserData/UserLibrary/Sets"
            if not os.path.exists(base_dir) and os.path.exists("examples/Sets"):
                base_dir = "examples/Sets"
            browser_html = generate_dir_html(
                base_dir,
                "",
                "/set-inspector",
                "set_path",
                "select_set",
            )
            return {
                "file_browser_html": browser_html,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "clip_options": options,
                "selected_clip": None,
                "notes": [],
                "envelopes": [],
                "region": 4.0,
                "browser_root": base_dir,
            }
        elif action == "show_clip":
            set_path = form.getvalue("set_path")
            clip_val = form.getvalue("clip_select")
            if not set_path or not clip_val:
                return self.format_error_response("Missing parameters")
            track_idx, clip_idx = map(int, clip_val.split(":"))
            result = get_clip_data(set_path, track_idx, clip_idx)
            if not result.get("success"):
                return self.format_error_response(result.get("message"))
            envelopes = result.get("envelopes", [])
            env_opts = "".join(
                f'<option value="{e.get("parameterId")}">{e.get("parameterId")}</option>'
                for e in envelopes
            )
            env_opts = '<option value="" disabled selected>-- Select Envelope --</option>' + env_opts
            return {
                "file_browser_html": None,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "clip_options": env_opts,
                "selected_clip": clip_val,
                "notes": result.get("notes", []),
                "envelopes": envelopes,
                "region": result.get("region", 4.0),
                "browser_root": None,
            }
        else:
            return self.format_error_response("Unknown action")
