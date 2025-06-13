from handlers.base_handler import BaseHandler
from core.set_inspector_handler import list_clips, get_clip_data, save_envelope
from core.list_msets_handler import list_msets
from core.pad_colors import rgb_string
from core.config import MSETS_DIRECTORY
import json
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

    def generate_clip_grid(self, clips, selected=None):
        """Return HTML for an 8x8 grid of clips including empty slots."""
        clip_map = {(c["track"], c["clip"]): c for c in clips}

        max_track = max([c["track"] for c in clips], default=-1)
        max_clip = max([c["clip"] for c in clips], default=-1)

        total_tracks = max(max_track + 1, 4)
        total_clips = max(max_clip + 1, 8)

        cells = []
        for track in range(total_tracks):
            for clip in range(total_clips):
                entry = clip_map.get((track, clip))
                value = f"{track}:{clip}"
                checked = ' checked' if selected == value else ''
                status = 'occupied' if entry else 'free'
                disabled = '' if entry else 'disabled'
                color_id = entry.get("color") if entry else None
                style = f' style="background-color: {rgb_string(int(color_id))}"' if color_id else ''
                name_attr = f' data-name="{entry.get("name", "")}"' if entry else ''
                cells.append(
                    f'<input type="radio" id="clip_{track}_{clip}" name="clip_select" value="{value}"{checked} {disabled}>'
                    f'<label for="clip_{track}_{clip}" class="pad-cell {status}"{style}{name_attr}></label>'
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
            "clip_grid": "",
            "clip_options": "",
            "selected_clip": None,
            "notes": [],
            "envelopes": [],
            "region": 4.0,
            "param_ranges_json": "{}",
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
            set_path = form.getvalue("set_path")
            if pad_val and pad_val.isdigit():
                idx = int(pad_val) - 1
                entry = next((m for m in msets if m.get("mset_id") == idx), None)
                if not entry:
                    return self.format_error_response("No set on selected pad", pad_grid=pad_grid)
                set_path = os.path.join(
                    MSETS_DIRECTORY,
                    entry["uuid"],
                    entry["mset_name"],
                    "Song.abl",
                )
            if not set_path:
                return self.format_error_response("No set selected", pad_grid=pad_grid)
            result = list_clips(set_path)
            if not result.get("success"):
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            clip_grid = self.generate_clip_grid(result.get("clips", []))
            set_name = os.path.basename(os.path.dirname(set_path))
            return {
                "pad_grid": pad_grid,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "set_name": set_name,
                "clip_grid": clip_grid,
                "selected_clip": None,
                "notes": [],
                "envelopes": [],
                "region": 4.0,
                "param_ranges_json": "{}",
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
            clip_info = list_clips(set_path)
            clip_grid = self.generate_clip_grid(clip_info.get("clips", []), selected=clip_val)
            envelopes = result.get("envelopes", [])
            param_map = result.get("param_map", {})
            param_meta = result.get("param_meta", {})

            def _label(e):
                meta = None
                if "parameterId" in e:
                    meta = param_meta.get(e["parameterId"])
                if not meta and "parameterIdName" in e:
                    meta = param_meta.get(e["parameterIdName"])
                if meta:
                    base = meta.get("deviceName") or ""
                    if meta.get("padName"):
                        return f"{base}: {meta['padName']}: {meta['name']}"
                    return f"{base}: {meta['name']}"
                key = e.get("parameterId") if "parameterId" in e else e.get("parameterIdName")
                return param_map.get(key, str(key))

            def _value(e):
                return e.get("parameterId") if "parameterId" in e else e.get("parameterIdName")

            env_opts = "".join(
                (
                    f'<option value="{_value(e)}">{_label(e)}</option>'
                )
                for e in envelopes
            )
            env_opts = '<option value="" disabled selected>-- Select Envelope --</option>' + env_opts
            set_name = os.path.basename(os.path.dirname(set_path))
            return {
                "pad_grid": pad_grid,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "set_name": set_name,
                "clip_grid": clip_grid,
                "clip_options": env_opts,
                "selected_clip": clip_val,
                "notes": result.get("notes", []),
                "envelopes": envelopes,
                "region": result.get("region", 4.0),
                "param_ranges_json": json.dumps(result.get("param_ranges", {})),
                "track_index": track_idx,
                "clip_index": clip_idx,
                "track_name": result.get("track_name"),
                "clip_name": result.get("clip_name"),
            }
        elif action == "save_envelope":
            set_path = form.getvalue("set_path")
            clip_val = form.getvalue("clip_select")
            param_val = form.getvalue("parameter_id")
            env_data = form.getvalue("envelope_data")
            if not (set_path and clip_val and param_val and env_data):
                return self.format_error_response("Missing parameters", pad_grid=pad_grid)
            track_idx, clip_idx = map(int, clip_val.split(":"))
            try:
                breakpoints = json.loads(env_data)
            except Exception:
                return self.format_error_response("Invalid envelope data", pad_grid=pad_grid)
            if param_val.isdigit():
                pid = int(param_val)
            else:
                pid = param_val
            result = save_envelope(set_path, track_idx, clip_idx, pid, breakpoints)
            if not result.get("success"):
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            clip_info = list_clips(set_path)
            clip_grid = self.generate_clip_grid(clip_info.get("clips", []), selected=clip_val)
            clip_data = get_clip_data(set_path, track_idx, clip_idx)
            envelopes = clip_data.get("envelopes", [])
            param_map = clip_data.get("param_map", {})
            param_meta = clip_data.get("param_meta", {})

            def _label(e):
                meta = None
                if "parameterId" in e:
                    meta = param_meta.get(e["parameterId"])
                if not meta and "parameterIdName" in e:
                    meta = param_meta.get(e["parameterIdName"])
                if meta:
                    base = meta.get("deviceName") or ""
                    if meta.get("padName"):
                        return f"{base}: {meta['padName']}: {meta['name']}"
                    return f"{base}: {meta['name']}"
                key = e.get("parameterId") if "parameterId" in e else e.get("parameterIdName")
                return param_map.get(key, str(key))

            def _value(e):
                return e.get("parameterId") if "parameterId" in e else e.get("parameterIdName")

            env_opts = "".join(
                (
                    f'<option value="{_value(e)}">{_label(e)}</option>'
                )
                for e in envelopes
            )
            env_opts = '<option value="" disabled selected>-- Select Envelope --</option>' + env_opts
            set_name = os.path.basename(os.path.dirname(set_path))
            return {
                "pad_grid": pad_grid,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "set_name": set_name,
                "clip_grid": clip_grid,
                "clip_options": env_opts,
                "selected_clip": clip_val,
                "notes": clip_data.get("notes", []),
                "envelopes": envelopes,
                "region": clip_data.get("region", 4.0),
                "param_ranges_json": json.dumps(clip_data.get("param_ranges", {})),
                "track_index": track_idx,
                "clip_index": clip_idx,
                "track_name": clip_data.get("track_name"),
                "clip_name": clip_data.get("clip_name"),
            }
        else:
            return self.format_error_response("Unknown action", pad_grid=pad_grid)
