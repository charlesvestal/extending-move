from handlers.base_handler import BaseHandler
from core.set_inspector_handler import list_clips, get_clip_data, save_envelope
from core.list_msets_handler import list_msets
from core.pad_colors import rgb_string
from core.config import MSETS_DIRECTORY
import json
import os

class SetInspectorHandler(BaseHandler):
    def generate_pad_grid(self, used_ids, color_map, name_map, selected_idx=None):
        """Return HTML for a 32-pad grid showing sets with colors.

        Args:
            used_ids (set): Pad indices that contain sets.
            color_map (dict): Mapping of pad index to pad color ID.
            name_map (dict): Mapping of pad index to set name.
            selected_idx (int, optional): Pad index to mark as selected.
        """
        cells = []
        for row in range(4):
            for col in range(8):
                idx = (3 - row) * 8 + col
                num = idx + 1
                has_set = idx in used_ids
                status = 'occupied' if has_set else 'free'
                disabled = '' if has_set else 'disabled'
                checked = ' checked' if selected_idx is not None and idx == selected_idx else ''
                color_id = color_map.get(idx)
                style = f' style="background-color: {rgb_string(color_id)}"' if color_id else ''
                name_attr = (
                    f" data-name=\"{name_map.get(idx, '')}\"" if idx in name_map else ""
                )
                cells.append(
                    f'<input type="radio" id="inspect_pad_{num}" name="pad_index" value="{num}"{checked} {disabled}>'
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
        selected_idx = None
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
            "loop_start": 0.0,
            "loop_end": 4.0,
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
                    pad_grid = self.generate_pad_grid(used, color_map, name_map)
                    return self.format_error_response("No set on selected pad", pad_grid=pad_grid)
                set_path = os.path.join(
                    MSETS_DIRECTORY,
                    entry["uuid"],
                    entry["mset_name"],
                    "Song.abl",
                )
                selected_idx = idx
            elif set_path:
                entry = next(
                    (m for m in msets if os.path.join(MSETS_DIRECTORY, m["uuid"], m["mset_name"], "Song.abl") == set_path),
                    None,
                )
                if entry:
                    selected_idx = int(entry.get("mset_id"))
            if not set_path:
                pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
                return self.format_error_response("No set selected", pad_grid=pad_grid)
            result = list_clips(set_path)
            if not result.get("success"):
                pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            clip_grid = self.generate_clip_grid(result.get("clips", []))
            set_name = os.path.basename(os.path.dirname(set_path))
            pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
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
                "loop_start": 0.0,
                "loop_end": 4.0,
                "param_ranges_json": "{}",
            }
        elif action == "show_clip":
            set_path = form.getvalue("set_path")
            clip_val = form.getvalue("clip_select")
            if not set_path or not clip_val:
                pad_grid = self.generate_pad_grid(used, color_map, name_map)
                return self.format_error_response("Missing parameters", pad_grid=pad_grid)
            entry = next(
                (m for m in msets if os.path.join(MSETS_DIRECTORY, m["uuid"], m["mset_name"], "Song.abl") == set_path),
                None,
            )
            if entry:
                selected_idx = int(entry.get("mset_id"))
            track_idx, clip_idx = map(int, clip_val.split(":"))
            result = get_clip_data(set_path, track_idx, clip_idx)
            if not result.get("success"):
                pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            clip_info = list_clips(set_path)
            clip_grid = self.generate_clip_grid(clip_info.get("clips", []), selected=clip_val)
            pitch_pad_val = form.getvalue("pitch_pad")
            pitch_pad = int(pitch_pad_val) if pitch_pad_val and pitch_pad_val.isdigit() else None
            notes = result.get("notes", [])
            from core.set_inspector_handler import extract_pitch_edit_notes
            pitch_pads = sorted(
                {
                    n.get("noteNumber")
                    for n in notes
                    if n.get("automations", {}).get("PitchBend")
                }
            )
            if pitch_pad is not None:
                notes = extract_pitch_edit_notes(notes, pitch_pad)
            pitch_opts = "<option value=''>Clip Notes</option>" + "".join(
                f"<option value='{pad}'" + (" selected" if pad == pitch_pad else "") + f">Pad {pad}</option>"
                for pad in pitch_pads
            )
            envelopes = result.get("envelopes", [])
            param_map = result.get("param_map", {})
            param_context = result.get("param_context", {})
            env_opts = "".join(
                (
                    f'<option value="{e.get("parameterId")}">'
                    f'{param_context.get(e.get("parameterId"), "Track")}: '
                    f'{param_map.get(e.get("parameterId"), e.get("parameterId"))}'
                    f'</option>'
                )
                for e in envelopes
            )
            env_opts = '<option value="">No Envelope</option>' + env_opts
            set_name = os.path.basename(os.path.dirname(set_path))
            pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
            return {
                "pad_grid": pad_grid,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "set_name": set_name,
                "clip_grid": clip_grid,
                "clip_options": env_opts,
                "selected_clip": clip_val,
                "notes": notes,
                "envelopes": envelopes,
                "region": result.get("region", 4.0),
                "loop_start": result.get("loop_start", 0.0),
                "loop_end": result.get("loop_end", 4.0),
                "param_ranges_json": json.dumps(result.get("param_ranges", {})),
                "track_index": track_idx,
                "clip_index": clip_idx,
                "track_name": result.get("track_name"),
                "clip_name": result.get("clip_name"),
                "pitch_opts": pitch_opts,
                "pitch_pad": pitch_pad,
            }
        elif action == "save_envelope":
            set_path = form.getvalue("set_path")
            clip_val = form.getvalue("clip_select")
            param_val = form.getvalue("parameter_id")
            env_data = form.getvalue("envelope_data")
            if not (set_path and clip_val and param_val and env_data):
                pad_grid = self.generate_pad_grid(used, color_map, name_map)
                return self.format_error_response("Missing parameters", pad_grid=pad_grid)
            entry = next(
                (m for m in msets if os.path.join(MSETS_DIRECTORY, m["uuid"], m["mset_name"], "Song.abl") == set_path),
                None,
            )
            if entry:
                selected_idx = int(entry.get("mset_id"))
            track_idx, clip_idx = map(int, clip_val.split(":"))
            try:
                breakpoints = json.loads(env_data)
            except Exception:
                pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
                return self.format_error_response("Invalid envelope data", pad_grid=pad_grid)
            result = save_envelope(set_path, track_idx, clip_idx, int(param_val), breakpoints)
            if not result.get("success"):
                pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            clip_info = list_clips(set_path)
            clip_grid = self.generate_clip_grid(clip_info.get("clips", []), selected=clip_val)
            clip_data = get_clip_data(set_path, track_idx, clip_idx)
            envelopes = clip_data.get("envelopes", [])
            param_map = clip_data.get("param_map", {})
            param_context = clip_data.get("param_context", {})
            selected_pid = int(param_val)
            env_opts = "".join(
                (
                    f'<option value="{e.get("parameterId")}"' +
                    (
                        ' selected' if e.get("parameterId") == selected_pid else ''
                    ) +
                    '>' +
                    f'{param_context.get(e.get("parameterId"), "Track")}: ' +
                    f'{param_map.get(e.get("parameterId"), e.get("parameterId"))}' +
                    '</option>'
                )
                for e in envelopes
            )
            env_opts = '<option value="">No Envelope</option>' + env_opts
            set_name = os.path.basename(os.path.dirname(set_path))
            pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
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
                "loop_start": clip_data.get("loop_start", 0.0),
                "loop_end": clip_data.get("loop_end", 4.0),
                "param_ranges_json": json.dumps(clip_data.get("param_ranges", {})),
                "track_index": track_idx,
                "clip_index": clip_idx,
                "track_name": clip_data.get("track_name"),
                "clip_name": clip_data.get("clip_name"),
            }
        elif action == "save_clip":
            set_path = form.getvalue("set_path")
            clip_val = form.getvalue("clip_select")
            notes_data = form.getvalue("clip_notes")
            env_data = form.getvalue("clip_envelopes")
            region_val = form.getvalue("region_end")
            loop_start_val = form.getvalue("loop_start")
            loop_end_val = form.getvalue("loop_end")
            if not (
                set_path
                and clip_val
                and notes_data is not None
                and env_data is not None
                and region_val is not None
                and loop_start_val is not None
                and loop_end_val is not None
            ):
                pad_grid = self.generate_pad_grid(used, color_map, name_map)
                return self.format_error_response("Missing parameters", pad_grid=pad_grid)
            entry = next(
                (m for m in msets if os.path.join(MSETS_DIRECTORY, m["uuid"], m["mset_name"], "Song.abl") == set_path),
                None,
            )
            if entry:
                selected_idx = int(entry.get("mset_id"))
            track_idx, clip_idx = map(int, clip_val.split(":"))
            try:
                notes = json.loads(notes_data)
                envelopes = json.loads(env_data)
                region_end = float(region_val)
                loop_start = float(loop_start_val)
                loop_end = float(loop_end_val)
            except Exception:
                pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
                return self.format_error_response("Invalid clip data", pad_grid=pad_grid)
            pitch_pad_val = form.getvalue("pitch_pad")
            pitch_pad = int(pitch_pad_val) if pitch_pad_val and pitch_pad_val.isdigit() else None
            from core.set_inspector_handler import save_clip, get_clip_data, apply_pitch_edit_changes
            if pitch_pad is not None:
                clip_data = get_clip_data(set_path, track_idx, clip_idx)
                if clip_data.get("success"):
                    notes = apply_pitch_edit_changes(clip_data.get("notes", []), pitch_pad, notes)
            
            result = save_clip(
                set_path,
                track_idx,
                clip_idx,
                notes,
                envelopes,
                region_end,
                loop_start,
                loop_end,
            )
            if not result.get("success"):
                pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
                return self.format_error_response(result.get("message"), pad_grid=pad_grid)
            clip_info = list_clips(set_path)
            clip_grid = self.generate_clip_grid(clip_info.get("clips", []), selected=clip_val)
            clip_data = get_clip_data(set_path, track_idx, clip_idx)
            envelopes = clip_data.get("envelopes", [])
            param_map = clip_data.get("param_map", {})
            param_context = clip_data.get("param_context", {})
            from core.set_inspector_handler import extract_pitch_edit_notes
            pitch_pads = sorted(
                {
                    n.get("noteNumber")
                    for n in clip_data.get("notes", [])
                    if n.get("automations", {}).get("PitchBend")
                }
            )
            pitch_opts = "<option value=''>Clip Notes</option>" + "".join(
                f"<option value='{pad}'" + (" selected" if pad == pitch_pad else "") + f">Pad {pad}</option>"
                for pad in pitch_pads
            )
            env_opts = "".join(
                (
                    f'<option value="{e.get("parameterId")}">' +
                    f'{param_context.get(e.get("parameterId"), "Track")}: ' +
                    f'{param_map.get(e.get("parameterId"), e.get("parameterId"))}' +
                    '</option>'
                )
                for e in envelopes
            )
            env_opts = '<option value="">No Envelope</option>' + env_opts
            set_name = os.path.basename(os.path.dirname(set_path))
            pad_grid = self.generate_pad_grid(used, color_map, name_map, selected_idx)
            return {
                "pad_grid": pad_grid,
                "message": result.get("message"),
                "message_type": "success",
                "selected_set": set_path,
                "set_name": set_name,
                "clip_grid": clip_grid,
                "clip_options": env_opts,
                "selected_clip": clip_val,
                "notes": notes if pitch_pad is None else extract_pitch_edit_notes(notes, pitch_pad),
                "envelopes": envelopes,
                "region": clip_data.get("region", 4.0),
                "loop_start": clip_data.get("loop_start", 0.0),
                "loop_end": clip_data.get("loop_end", 4.0),
                "param_ranges_json": json.dumps(clip_data.get("param_ranges", {})),
                "track_index": track_idx,
                "clip_index": clip_idx,
                "track_name": clip_data.get("track_name"),
                "clip_name": clip_data.get("clip_name"),
                "pitch_opts": pitch_opts,
                "pitch_pad": pitch_pad,
            }
        else:
            return self.format_error_response("Unknown action", pad_grid=pad_grid)
