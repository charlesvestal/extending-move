from handlers.base_handler import BaseHandler
import os
import zipfile
import tempfile
import shutil
import logging
from core.set_management_handler import (
    create_set, generate_midi_set_from_file, generate_drum_set_from_file,
    generate_c_major_chord_example, generate_multichannel_midi_set,
    assign_midi_to_track
)
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle
from core.pad_colors import PAD_COLORS, PAD_COLOR_LABELS
import json

logger = logging.getLogger(__name__)

class SetManagementHandler(BaseHandler):
    def handle_get(self):
        """
        Return context for rendering the MIDI Upload page.
        """
        # Get available pads
        msets, ids = list_msets(return_free_ids=True)
        free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
        pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in free_pads)
        pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + pad_options
        pad_color_options = self.generate_color_options()
        color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
        name_map = {int(m["mset_id"]): m["mset_name"] for m in msets}
        bpm_map = {int(m["mset_id"]): str(m["bpm"]) for m in msets if m.get("bpm")}
        pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, name_map, bpm_map, free_only=True)
        # Get existing sets for dropdown
        existing_sets = [(m["mset_name"], m.get("bpm", "—")) for m in msets]
        existing_set_options = '<option value="" disabled selected>-- Select Existing Set --</option>'
        for name, bpm in sorted(existing_sets):
            existing_set_options += f'<option value="{name}">{name} ({bpm} BPM)</option>'
        
        return {
            'pad_options': pad_options,
            'pad_color_options': pad_color_options,
            'pad_grid': pad_grid,
            'existing_set_options': existing_set_options,
            'message': 'Upload a MIDI file to generate a set',
            'message_type': 'info'
        }

    def handle_post(self, form):
        """
        Handle POST request for set management operations.
        """
        action = form.getvalue('action', 'create')

        # Get pad options for error responses
        msets, ids = list_msets(return_free_ids=True)
        free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
        pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in free_pads)
        pad_color_options = self.generate_color_options()
        color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
        name_map = {int(m["mset_id"]): m["mset_name"] for m in msets}
        bpm_map = {int(m["mset_id"]): str(m["bpm"]) for m in msets if m.get("bpm")}
        pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, name_map, bpm_map, free_only=True)
        # Get existing sets for dropdown
        existing_sets = [(m["mset_name"], m.get("bpm", "—")) for m in msets]
        existing_set_options = '<option value="" disabled selected>-- Select Existing Set --</option>'
        for name, bpm in sorted(existing_sets):
            existing_set_options += f'<option value="{name}">{name} ({bpm} BPM)</option>'

        if action == 'upload_midi':
            # Generate set from uploaded MIDI file
            set_name = form.getvalue('set_name', '')
            midi_type = form.getvalue('midi_type', 'melodic')
            
            # For assign-to-track with existing set, we don't need set_name
            if midi_type == 'assigntotrack':
                set_mode = form.getvalue('set_mode', 'new')
                if set_mode == 'new' and not set_name:
                    return self.format_error_response(
                        "Please enter a name for the new set",
                        pad_options=pad_options,
                        pad_color_options=pad_color_options,
                        pad_grid=pad_grid,
                        existing_set_options=existing_set_options,
                    )
                # For existing set mode, we'll validate existing_set_name later
            elif not set_name:
                # For non-assign-to-track modes, set_name is always required
                return self.format_error_response(
                    "Missing required parameter: set_name",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                    existing_set_options=existing_set_options,
                )
            
            # Handle file upload
            if 'midi_file' not in form:
                return self.format_error_response(
                    "No MIDI file uploaded",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                    existing_set_options=existing_set_options,
                )
            
            fileitem = form['midi_file']
            if not fileitem.filename:
                return self.format_error_response(
                    "No MIDI file selected",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                    existing_set_options=existing_set_options,
                )
            
            # Check file extension
            filename = fileitem.filename.lower()
            if not (filename.endswith('.mid') or filename.endswith('.midi')):
                return self.format_error_response(
                    "Invalid file type. Please upload a .mid or .midi file",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                    existing_set_options=existing_set_options,
                )
            
            # Save uploaded file temporarily
            success, filepath, error_response = self.handle_file_upload(form, 'midi_file')
            if not success:
                return self.format_error_response(
                    error_response.get('message', "Failed to upload MIDI file"),
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    pad_grid=pad_grid,
                    existing_set_options=existing_set_options,
                )
            
            try:
                # Get tempo if provided
                tempo_str = form.getvalue('tempo')
                tempo = float(tempo_str) if tempo_str and tempo_str.strip() else None

                # Dispatch based on MIDI type
                midi_type = form.getvalue('midi_type', 'melodic')
                if midi_type == 'drum':
                    result = generate_drum_set_from_file(set_name, filepath, tempo)
                elif midi_type == 'multichannel':
                    result = generate_multichannel_midi_set(set_name, filepath, tempo)
                elif midi_type == 'assigntotrack':
                    # Handle assign to track mode
                    target_track_str = form.getvalue('target_track', '1')
                    target_track = int(target_track_str) if target_track_str.isdigit() else 1
                    set_mode = form.getvalue('set_mode', 'new')
                    
                    if set_mode == 'existing':
                        # Use existing set name from dropdown
                        existing_set_name = form.getvalue('existing_set_name', '')
                        if not existing_set_name:
                            return self.format_error_response(
                                "Please select an existing set",
                                pad_options=pad_options,
                                pad_color_options=pad_color_options,
                                pad_grid=pad_grid,
                                existing_set_options=existing_set_options,
                            )
                        # Find the set's UUID to construct correct path
                        existing_uuid = None
                        for m in msets:
                            if m["mset_name"] == existing_set_name:
                                existing_uuid = m["uuid"]
                                break
                        if existing_uuid:
                            existing_path = os.path.join("/data/UserData/UserLibrary/Sets", existing_uuid, existing_set_name, "Song.abl")
                        else:
                            # Fallback - try direct path
                            existing_path = os.path.join("/data/UserData/UserLibrary/Sets", existing_set_name)
                            if not existing_path.endswith('.abl'):
                                existing_path += '.abl'
                        # Use the existing set name for saving
                        final_set_name = existing_set_name
                    else:
                        # Create new set - name already validated above
                        existing_path = None
                        final_set_name = set_name
                    
                    result = assign_midi_to_track(final_set_name, filepath, target_track, existing_path, tempo)
                else:
                    result = generate_midi_set_from_file(set_name, filepath, tempo)

            finally:
                # Clean up uploaded file
                self.cleanup_upload(filepath)

        else:
            return self.format_error_response(
                f"Unknown action: {action}",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
            )

        # Check if the operation was successful
        if not result.get('success'):
            return self.format_error_response(
                result.get('message', 'Operation failed'),
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options,
            )

        # Check if this is "add to existing set" mode - skip restore/bundle
        is_add_to_existing = (
            midi_type == 'assigntotrack' and
            form.getvalue('set_mode', 'new') == 'existing'
        )

        if is_add_to_existing:
            # For existing set mode, file is already saved - just return success
            # The set stays on its original pad
            return self.format_success_response(
                f"MIDI assigned to {form.getvalue('target_track', '1')} in existing set '{form.getvalue('existing_set_name', '')}'",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options
            )

        # Parse pad assignment (only for new set creation)
        pad_selected = form.getvalue('pad_index')
        pad_color = form.getvalue('pad_color')
        if not pad_selected or not pad_selected.isdigit():
            return self.format_error_response(
                "Invalid pad selection",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options,
            )
        if not pad_color or not pad_color.isdigit():
            return self.format_error_response(
                "Invalid pad color",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options,
            )
        pad_selected_int = int(pad_selected) - 1
        pad_color_int = int(pad_color)
        # Prepare bundling of generated set
        set_path = result.get('path')
        if not set_path:
            return self.format_error_response(
                "Internal error: missing set path",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options,
            )
        # Create temp directory for bundling
        with tempfile.TemporaryDirectory() as tmpdir:
            song_abl_path = os.path.join(tmpdir, 'Song.abl')
            shutil.copy(set_path, song_abl_path)
            # Name bundle based on set name without .abl extension
            base_path, _ = os.path.splitext(set_path)
            bundle_path = base_path + '.ablbundle'
            with zipfile.ZipFile(bundle_path, 'w') as zf:
                zf.write(song_abl_path, 'Song.abl')
            # Restore to device
            restore_result = restore_ablbundle(bundle_path, pad_selected_int, pad_color_int)
            os.remove(bundle_path)

        if restore_result.get('success'):
            # Clean up the original .abl file after successful placement
            try:
                os.remove(set_path)
            except Exception as e:
                logger.warning("Failed to clean up set file %s: %s", set_path, e)

            # Refresh pad list after successful placement
            msets_updated, updated_ids = list_msets(return_free_ids=True)
            updated_free_pads = sorted([pad_id + 1 for pad_id in updated_ids.get("free", [])])
            updated_pad_options = ''.join(f'<option value="{pad}">{pad}</option>' for pad in updated_free_pads)
            updated_pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + updated_pad_options
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets_updated if str(m["mset_color"]).isdigit()}
            name_map = {int(m["mset_id"]): m["mset_name"] for m in msets_updated}
            bpm_map = {int(m["mset_id"]): str(m["bpm"]) for m in msets_updated if m.get("bpm")}
            pad_grid = self.generate_pad_grid(updated_ids.get("used", set()), color_map, name_map, bpm_map, free_only=True)
            return self.format_success_response(restore_result['message'], pad_options=updated_pad_options, pad_color_options=pad_color_options, pad_grid=pad_grid, existing_set_options=existing_set_options)
        else:
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            name_map = {int(m["mset_id"]): m["mset_name"] for m in msets}
            bpm_map = {int(m["mset_id"]): str(m["bpm"]) for m in msets if m.get("bpm")}
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, name_map, bpm_map, free_only=True)
            return self.format_error_response(restore_result.get('message'), pad_options=pad_options, pad_color_options=pad_color_options, pad_grid=pad_grid, existing_set_options=existing_set_options)

    def generate_color_options(self, input_name="pad_color", pad_input_name="pad_index"):
        """Return HTML for the custom color dropdown with pad preview."""
        colors = [PAD_COLORS[i] for i in sorted(PAD_COLORS)]
        names = [PAD_COLOR_LABELS[i] for i in sorted(PAD_COLOR_LABELS)]
        dropdown_id = f"{input_name}_dropdown"
        colors_json = json.dumps(colors)
        names_json = json.dumps(names)
        return (
            f'<div class="color-dropdown" id="{dropdown_id}">'
            f'<div class="dropdown-toggle">'
            f'<span class="preview-square"></span>'
            f'<span class="preview-label"></span>'
            f'<span class="arrow">&#9662;</span>'
            f'</div>'
            f'<div class="dropdown-menu"></div>'
            f'<input type="hidden" name="{input_name}" value="1">'
            f'</div>'
            f'<script>'
            f'const colors_{dropdown_id} = {colors_json};'
            f'const names_{dropdown_id} = {names_json};'
            f'(function() {{'
            f' document.addEventListener("DOMContentLoaded", function() {{'
            f' const c = colors_{dropdown_id};'
            f' const n = names_{dropdown_id};'
            f' const container = document.getElementById("{dropdown_id}");'
            f' const toggle = container.querySelector(".dropdown-toggle");'
            f' const menu = container.querySelector(".dropdown-menu");'
            f' const hidden = container.querySelector("input");'
            f' const padName = "{pad_input_name}";'
            f' let open = false;'
            f' let selected = parseInt(hidden.value) - 1;'
            f' function render() {{'
            f'  menu.innerHTML = "";'
            f'  c.forEach((col, idx) => {{'
            f'    const item = document.createElement("div");'
            f'    item.className = "dropdown-item";'
            f'    item.innerHTML = `<span class="preview-square" style="background-color: rgb(${{col[0]}}, ${{col[1]}}, ${{col[2]}});"></span> <span class="label">${{n[idx]}}</span>`;'
            f'    item.addEventListener("click", () => {{selected = idx; hidden.value = idx + 1; update(); close();}});'
            f'    menu.appendChild(item);'
            f'  }});'
            f' }}'
            f' function previewPad() {{'
            f'  const radios = document.querySelectorAll(`input[name="${{padName}}"]`);'
            f'  radios.forEach(r => {{'
            f'    const lab = document.querySelector(`label[for="${{r.id}}"]`);'
            f'    if(lab && !r.checked && !r.disabled) lab.style.backgroundColor = "";'
            f'  }});'
            f'  const checked = document.querySelector(`input[name="${{padName}}"]:checked`);'
            f'  if(checked) {{'
            f'    const lab = document.querySelector(`label[for="${{checked.id}}"]`);'
            f'    if(lab) {{ const col = c[selected]; lab.style.backgroundColor = `rgb(${{col[0]}}, ${{col[1]}}, ${{col[2]}})`; }}'
            f'  }}'
            f' }}'
            f' function update() {{'
            f'  const col = c[selected];'
            f'  toggle.querySelector(".preview-square").style.backgroundColor = `rgb(${{col[0]}}, ${{col[1]}}, ${{col[2]}})`;'
            f'  toggle.querySelector(".preview-label").textContent = n[selected];'
            f'  previewPad();'
            f' }}'
            f' function openMenu() {{ menu.style.display = "block"; open = true; }}'
            f' function close() {{ menu.style.display = "none"; open = false; }}'
            f' toggle.addEventListener("click", e => {{ e.stopPropagation(); open ? close() : openMenu(); }});'
            f' document.addEventListener("click", e => {{ if (open && !container.contains(e.target)) close(); }});'
            f' document.querySelectorAll(`input[name="${{padName}}"]`).forEach(r => r.addEventListener("change", previewPad));'
            f' render(); update(); close();'
            f' }});'
            f'}})();'
            f'</script>'
            f'<style>'
            f'.color-dropdown {{ position: relative; width: 200px; font-size: 0.875rem; }}'
            f'.color-dropdown .dropdown-toggle {{ border: 1px solid #ddd; border-radius: 4px; padding: 0.5rem; cursor: pointer; display: flex; align-items: center; background: #fff; }}'
            f'.color-dropdown .preview-square {{ width: 16px; height: 16px; margin-right: 8px; border: 1px solid #ccc; }}'
            f'.color-dropdown .arrow {{ margin-left: auto; }}'
            f'.color-dropdown .dropdown-menu {{ position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #ddd; border-radius: 4px; max-height: 200px; overflow-y: auto; z-index: 1000; }}'
            f'.color-dropdown .dropdown-item {{ padding: 0.5rem; display: flex; align-items: center; cursor: pointer; }}'
            f'.color-dropdown .dropdown-item:hover {{ background-color: #f0f0f0; }}'
            f'.color-dropdown .dropdown-item .preview-square {{ margin-right: 8px; }}'
            f'</style>'
        )
