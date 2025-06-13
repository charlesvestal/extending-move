from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.set_inspector_handler import (
    list_clips,
    get_clip_data,
    get_set_pad_info,
    build_clip_grid_html,
)
from core.list_msets_handler import list_msets
from core.pad_colors import rgb_string
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
            "clip_grid": None,
            "pad_grid": None,
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

            clips = result.get("clips", [])
            clip_grid = build_clip_grid_html(clips, set_path)

            msets, ids = list_msets(return_free_ids=True)
            color_map = {
                int(m["mset_id"]): int(m["mset_color"])
                for m in msets
                if str(m["mset_color"]).isdigit()
            }
            pad_info = get_set_pad_info(set_path)
            pad_index = pad_info.get("pad")
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, pad_index)

            return {
                "file_browser_html": browser_html,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "clip_grid": clip_grid,
                "pad_grid": pad_grid,
                "clip_options": "",
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
            clips_res = list_clips(set_path)
            clips = clips_res.get("clips", []) if clips_res.get("success") else []
            clip_grid = build_clip_grid_html(clips, set_path)

            msets, ids = list_msets(return_free_ids=True)
            color_map = {
                int(m["mset_id"]): int(m["mset_color"])
                for m in msets
                if str(m["mset_color"]).isdigit()
            }
            pad_info = get_set_pad_info(set_path)
            pad_index = pad_info.get("pad")
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, pad_index)

            return {
                "file_browser_html": None,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "clip_options": env_opts,
                "selected_clip": clip_val,
                "clip_grid": clip_grid,
                "pad_grid": pad_grid,
                "notes": result.get("notes", []),
                "envelopes": envelopes,
                "region": result.get("region", 4.0),
                "browser_root": None,
            }
        else:
            return self.format_error_response("Unknown action")

    def generate_pad_grid(self, used_ids, color_map, active=None):
        """Return HTML pad grid with the active pad highlighted."""
        cells = []
        for row in range(4):
            for col in range(8):
                idx = (3 - row) * 8 + col
                num = idx + 1
                occupied = idx in used_ids
                status = "occupied" if occupied else "free"
                color_id = color_map.get(idx)
                style = f' style="background-color: {rgb_string(color_id)}"' if color_id else ''
                checked = " checked" if active is not None and idx == active else ""
                cells.append(
                    f'<input type="radio" id="insp_pad_{num}" name="pad" value="{num}" disabled{checked}>'
                    f'<label for="insp_pad_{num}" class="pad-cell {status}"{style}></label>'
                )
        return '<div class="pad-grid">' + ''.join(cells) + '</div>'
