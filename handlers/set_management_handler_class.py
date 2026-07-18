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
from core.refresh_handler import refresh_library
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
        # Generate color dropdown with swatches for clip color (same visual style as pad color)
        clip_color_options = self.generate_color_options(input_name="clip_color")
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
            'clip_color_options': clip_color_options,
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
        pad_options = '<option value="" disabled selected>-- Select Pad --</option>' + pad_options
        pad_color_options = self.generate_color_options()
        # Generate color dropdown with swatches for clip color
        clip_color_options = self.generate_color_options(input_name="clip_color")
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
            # Handle multi-file MIDI upload with track assignments
            set_name = form.getvalue('set_name', '')
            set_mode = form.getvalue('set_mode', 'new')
            midi_type = form.getvalue('midi_type', 'melodic')
            
            # Drum mode always creates a new set
            if midi_type == 'drum':
                set_mode = 'new'
            
            # Validate set name for new sets
            pad_color_for_clip = None
            if set_mode == 'new':
                if not set_name:
                    return self.format_error_response(
                        "Please enter a name for the new set",
                        pad_options=pad_options,
                        pad_color_options=pad_color_options,
                        clip_color_options=clip_color_options,
                        pad_grid=pad_grid,
                        existing_set_options=existing_set_options,
                    )
                # Get pad color early for new sets (will be used as clip color)
                pad_color_str = form.getvalue('pad_color', '1')
                pad_color_for_clip = int(pad_color_str) if pad_color_str and pad_color_str.isdigit() else 1
            
            # Validate existing set selection for existing mode
            existing_path = None
            final_set_name = set_name
            if set_mode == 'existing':
                existing_set_name = form.getvalue('existing_set_name', '')
                if not existing_set_name:
                    return self.format_error_response(
                        "Please select an existing set",
                        pad_options=pad_options,
                        pad_color_options=pad_color_options,
                        clip_color_options=clip_color_options,
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
                    return self.format_error_response(
                        f"Could not find set '{existing_set_name}' in the library. It may have been renamed or removed.",
                        pad_options=pad_options,
                        pad_color_options=pad_color_options,
                        clip_color_options=clip_color_options,
                        pad_grid=pad_grid,
                        existing_set_options=existing_set_options,
                    )
                final_set_name = existing_set_name
            
            # Handle file uploads - support multiple files
            file_list = []
            if 'midi_files' in form:
                # Handle multiple files - form['midi_files'] is now a list of FileField objects
                files = form['midi_files']
                if not isinstance(files, list):
                    files = [files]
                for i, fileitem in enumerate(files):
                    if hasattr(fileitem, 'filename') and fileitem.filename:
                        # Server-side extension validation
                        if not fileitem.filename.lower().endswith(('.mid', '.midi')):
                            return self.format_error_response(
                                f"File '{fileitem.filename}' is not a MIDI file. Only .mid and .midi files are accepted.",
                                pad_options=pad_options,
                                pad_color_options=pad_color_options,
                                clip_color_options=clip_color_options,
                                pad_grid=pad_grid,
                                existing_set_options=existing_set_options,
                            )
                        file_list.append((i, fileitem))
            
            if not file_list:
                return self.format_error_response(
                    "No MIDI files uploaded",
                    pad_options=pad_options,
                    pad_color_options=pad_color_options,
                    clip_color_options=clip_color_options,
                    pad_grid=pad_grid,
                    existing_set_options=existing_set_options,
                )
            
            # Get clip color for existing sets (new sets use pad_color_for_clip per file)
            clip_color = None
            if set_mode == 'existing':
                clip_color_str = form.getvalue('clip_color', '1')
                clip_color = int(clip_color_str) if clip_color_str.isdigit() else 1
            
            # Get tempo if provided
            tempo_str = form.getvalue('tempo')
            tempo = float(tempo_str) if tempo_str and tempo_str.strip() else None
            
            # Drum import: single file, 808 pad mapping
            if midi_type == 'drum':
                temp_files = []
                try:
                    i, fileitem = file_list[0]
                    success, filepath, error_response = self.save_uploaded_file(fileitem)
                    if not success:
                        result = {'success': False, 'message': f"Upload failed: {error_response.get('message', 'Unknown error')}"}
                    else:
                        temp_files.append(filepath)
                        result = generate_drum_set_from_file(set_name, filepath, tempo=tempo)
                        result['filename'] = fileitem.filename
                finally:
                    for fp in temp_files:
                        self.cleanup_upload(fp)
            
            # Melodic import: multi-file, per-track assignment
            else:
                # Process each file with its track assignment
                temp_files = []
                results = []
                try:
                    for i, fileitem in file_list:
                        # Get track assignment for this file
                        track_str = form.getvalue(f'track_{i}', '1')
                        target_track = int(track_str) if track_str.isdigit() else 1
                        
                        # Save uploaded file temporarily
                        success, filepath, error_response = self.save_uploaded_file(fileitem)
                        if not success:
                            results.append({'success': False, 'message': f"File {fileitem.filename}: {error_response.get('message', 'Upload failed')}"})
                            continue
                        
                        temp_files.append(filepath)
                        
                        # Determine clip color for this file
                        file_clip_color = clip_color if set_mode == 'existing' else pad_color_for_clip
                        
                        # Process the MIDI file
                        result = assign_midi_to_track(final_set_name, filepath, target_track, existing_path, tempo, file_clip_color)
                        result['filename'] = fileitem.filename
                        result['track'] = target_track
                        results.append(result)
                        
                        # For subsequent files, use the updated existing_path (set was created/modified)
                        if existing_path is None and result.get('success'):
                            # First file created the set, update path for subsequent files
                            output_dir = "/data/UserData/UserLibrary/Sets"
                            existing_path = os.path.join(output_dir, final_set_name)
                            if not existing_path.endswith('.abl'):
                                existing_path += '.abl'
                    
                    # Aggregate results
                    success_count = sum(1 for r in results if r.get('success'))
                    failure_count = len(results) - success_count
                    
                    if failure_count == 0:
                        # All succeeded
                        if len(results) == 1:
                            result = results[0]
                        else:
                            # Build summary message
                            track_summary = []
                            for r in results:
                                track_summary.append(f"{r['filename']} → Track {r['track']}")
                            result = {
                                'success': True,
                                'message': f"Successfully imported {success_count} file(s): " + ", ".join(track_summary),
                                'path': results[0].get('path')  # Include path from first result for new set bundling
                            }
                    elif success_count == 0:
                        # All failed
                        errors = [f"{r['filename']}: {r.get('message', 'Unknown error')}" for r in results]
                        result = {
                            'success': False,
                            'message': "All imports failed: " + "; ".join(errors)
                        }
                    else:
                        # Mixed results - report as error so user sees red banner
                        success_files = [r['filename'] for r in results if r.get('success')]
                        failed_files = [f"{r['filename']}: {r.get('message', 'Unknown error')}" for r in results if not r.get('success')]
                        # Find path from first successful result
                        first_success_path = None
                        for r in results:
                            if r.get('success') and r.get('path'):
                                first_success_path = r.get('path')
                                break
                        result = {
                            'success': False,
                            'message': f"Partial failure: {success_count} succeeded ({', '.join(success_files)}), {failure_count} failed ({'; '.join(failed_files)})",
                            'path': first_success_path
                        }
                
                finally:
                    # Clean up all temporary files
                    for filepath in temp_files:
                        self.cleanup_upload(filepath)

        else:
            return self.format_error_response(
                f"Unknown action: {action}",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                clip_color_options=clip_color_options,
                pad_grid=pad_grid,
            )

        # Check if the operation was successful
        if not result.get('success'):
            return self.format_error_response(
                result.get('message', 'Operation failed'),
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                clip_color_options=clip_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options,
            )

        # Check if this is "add to existing set" mode - skip restore/bundle
        is_add_to_existing = set_mode == 'existing'

        if is_add_to_existing:
            # For existing set mode, file is already saved - refresh library so Move picks up the change
            refresh_library()
            existing_set_name = form.getvalue('existing_set_name', '')
            return self.format_success_response(
                f"{result.get('message', 'MIDI imported')} in existing set '{existing_set_name}'",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                clip_color_options=clip_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options
            )

        # For new set creation, check if any files succeeded (path is required)
        set_path = result.get('path')
        if not set_path:
            # All files failed - return the error without trying to bundle
            return self.format_error_response(
                result.get('message', 'Failed to create set'),
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                clip_color_options=clip_color_options,
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
                clip_color_options=clip_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options,
            )
        if not pad_color or not pad_color.isdigit():
            return self.format_error_response(
                "Invalid pad color",
                pad_options=pad_options,
                pad_color_options=pad_color_options,
                clip_color_options=clip_color_options,
                pad_grid=pad_grid,
                existing_set_options=existing_set_options,
            )
        pad_selected_int = int(pad_selected) - 1
        pad_color_int = int(pad_color)
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
            return self.format_success_response(restore_result['message'], pad_options=updated_pad_options, pad_color_options=pad_color_options, clip_color_options=clip_color_options, pad_grid=pad_grid, existing_set_options=existing_set_options)
        else:
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            name_map = {int(m["mset_id"]): m["mset_name"] for m in msets}
            bpm_map = {int(m["mset_id"]): str(m["bpm"]) for m in msets if m.get("bpm")}
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, name_map, bpm_map, free_only=True)
            return self.format_error_response(restore_result.get('message'), pad_options=pad_options, pad_color_options=pad_color_options, clip_color_options=clip_color_options, pad_grid=pad_grid, existing_set_options=existing_set_options)

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
