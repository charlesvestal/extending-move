from handlers.base_handler import BaseHandler
from core.set_inspector_handler import list_clips, get_clip_data
from core.list_msets_handler import list_msets
from core.pad_colors import rgb_string
from core.config import MSETS_DIRECTORY
import os

class SetInspectorHandler(BaseHandler):
    def generate_pad_grid(self, used_ids, color_map, name_map):
        """Return HTML for a 32-pad grid showing sets with colors.

        Args:
            used_ids (set): Pad indices that contain sets.
            color_map (dict): Mapping of pad index to pad color ID.
            name_map (dict): Mapping of pad index to set name.
        """
        cells = []
        for row in range(4):
            for col in range(8):
                idx = (3 - row) * 8 + col
                num = idx + 1
                has_set = idx in used_ids
                status = 'occupied' if has_set else 'free'
                disabled = '' if has_set else 'disabled'
                color_id = color_map.get(idx)
                style = f' style="background-color: {rgb_string(color_id)}"' if color_id else ''
                name_attr = (
                    f" data-name=\"{name_map.get(idx, '')}\"" if idx in name_map else ""
                )
                cells.append(
                    f'<input type="radio" id="inspect_pad_{num}" name="pad_index" value="{num}" {disabled}>'
                    f'<label for="inspect_pad_{num}" class="pad-cell {status}"{style}{name_attr}></label>'
                )
        return '<div class="pad-grid">' + ''.join(cells) + '</div>'

    def generate_clip_grid(self, clips):
        """Return HTML for an 32-cell grid showing clips by track.

        Each row corresponds to a track (starting at 1) and each column to a
        clip index within that track. Cells without clips are disabled.

        Args:
            clips (list): List of clip dictionaries with ``track`` and ``clip``
                keys as returned by :func:`list_clips`.
        """
        # Organize clips by track and clip index for easy lookup
        track_map = {}
        for c in clips:
            t = int(c.get("track", 0))
            slot = int(c.get("clip", 0))
            track_map.setdefault(t, {})[slot] = c.get("name", f"{t}:{slot}")

        cells = []
        for row in range(4):  # show up to 4 tracks
            for col in range(8):  # show up to 8 clips per track
                clip_name = track_map.get(row, {}).get(col)
                disabled = "" if clip_name else "disabled"
                status = "occupied" if clip_name else "free"
                value = f"{row}:{col}" if clip_name else ""
                label = clip_name if clip_name else ""
                cell_id = f"clip_{row}_{col}"
                cells.append(
                    f'<input type="radio" id="{cell_id}" '
                    f'name="clip_select" value="{value}" {disabled}>'
                    f'<label for="{cell_id}" class="pad-cell {status}">{label}</label>'
                )
        return '<div class="pad-grid">' + ''.join(cells) + '</div>'

    def handle_get(self):
        msets, ids = list_msets(return_free_ids=True)
        used = ids.get("used", set())
        color_map = {
            int(m["mset_id"]): int(m["mset_color"])
            for m in msets
            if str(m["mset_color"]).isdigit()
        }
        name_map = {int(m["mset_id"]): m["mset_name"] for m in msets}
        pad_grid = self.generate_pad_grid(used, color_map, name_map)
        return {
            "pad_grid": pad_grid,
            "message": "Select a set to inspect",
            "message_type": "info",
            "selected_set": None,
            "clip_options": "",
            "selected_clip": None,
            "notes": [],
            "envelopes": [],
            "region": 4.0,
        }

    def handle_post(self, form):
        action = form.getvalue("action")
        msets, ids = list_msets(return_free_ids=True)
        used = ids.get("used", set())
        color_map = {
            int(m["mset_id"]): int(m["mset_color"])
            for m in msets
            if str(m["mset_color"]).isdigit()
        }
        name_map = {int(m["mset_id"]): m["mset_name"] for m in msets}
        pad_grid = self.generate_pad_grid(used, color_map, name_map)

        if action == "select_set":
            pad_val = form.getvalue("pad_index")
            if not pad_val or not pad_val.isdigit():
                return self.format_error_response("No set selected", pad_grid=pad_grid)
            idx = int(pad_val) - 1
            entry = next((m for m in msets if m.get("mset_id") == idx), None)
            if not entry:
                return self.format_error_response("No set on selected pad", pad_grid=pad_grid)
            set_path = os.path.join(MSETS_DIRECTORY, entry["uuid"], entry["mset_name"], "Song.abl")
            result = list_clips(set_path)
            if not result.get("success"):
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            clip_grid = self.generate_clip_grid(result.get("clips", []))
            return {
                "pad_grid": pad_grid,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "clip_grid": clip_grid,
                "selected_clip": None,
                "notes": [],
                "envelopes": [],
                "region": 4.0,
            }
        elif action == "show_clip":
            set_path = form.getvalue("set_path")
            clip_val = form.getvalue("clip_select")
            if not set_path or not clip_val:
                return self.format_error_response("Missing parameters", pad_grid=pad_grid)
            track_idx, clip_idx = map(int, clip_val.split(":"))
            result = get_clip_data(set_path, track_idx, clip_idx)
            if not result.get("success"):
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            envelopes = result.get("envelopes", [])
            env_opts = "".join(
                f'<option value="{e.get("parameterId")}">{e.get("parameterId")}</option>'
                for e in envelopes
            )
            env_opts = '<option value="" disabled selected>-- Select Envelope --</option>' + env_opts
            return {
                "pad_grid": pad_grid,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "clip_options": env_opts,
                "selected_clip": clip_val,
                "notes": result.get("notes", []),
                "envelopes": envelopes,
                "region": result.get("region", 4.0),
            }
        else:
            return self.format_error_response("Unknown action", pad_grid=pad_grid)
