import os
import logging
from handlers.base_handler import BaseHandler
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle
from core.pad_colors import PAD_COLORS, PAD_COLOR_LABELS, rgb_string
import json

class RestoreHandler(BaseHandler):
    """
    Handles web requests for set restore.
    """

    def handle_get(self):
        """
        Handles GET requests to display available pads for restoration.

        Returns:
            dict: Context for rendering the restore.html template.
        """
        try:
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            logging.info(f"Available Pads: {free_pads}")

            return {
                "options": self.generate_pad_options(free_pads),
                "color_options": self.generate_color_options(),
                "pad_grid": pad_grid,
                "message": f"Available pads: {', '.join(map(str, free_pads))}" if free_pads else "No pads available."
            }
        
        except Exception as e:
            logging.error(f"Error retrieving free pads: {str(e)}")
            return {
                "options": '<option value="" disabled>Error loading pads</option>',
                "color_options": self.generate_color_options(),
                "pad_grid": '<div class="pad-grid"></div>',
                "message": "Error retrieving available pads."
            }

    def handle_post(self, form):
        """
        Handles POST requests to restore an uploaded .ablbundle file.
        """
        valid, error_response = self.validate_action(form, "restore_ablbundle")
        if not valid:
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            error_response["options"] = options
            error_response["color_options"] = self.generate_color_options()
            error_response["pad_grid"] = pad_grid
            return error_response

        pad_selected = form.getvalue("mset_index")
        pad_color = form.getvalue("mset_color")

        # Early validation: pad index
        if not pad_selected or not pad_selected.isdigit():
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            return self.format_error_response("Invalid pad selection provided.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())
        # Early validation: color
        if not pad_color or not pad_color.isdigit():
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            return self.format_error_response("Invalid pad color provided.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())

        pad_selected = int(pad_selected) - 1  # Convert back to internal ID
        pad_color = int(pad_color)

        if not (0 <= pad_selected <= 31):
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            return self.format_error_response("Invalid pad selection. Must be between 1 and 32.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())
        if not (1 <= pad_color <= 25):
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            return self.format_error_response("Invalid pad color. Must be between 1 and 25.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())

        success, filepath, error_response = self.handle_file_upload(form, "ablbundle")
        if not success:
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            if error_response is None:
                error_response = {}
            error_response["options"] = options
            error_response["color_options"] = self.generate_color_options()
            error_response["pad_grid"] = pad_grid
            return error_response

        try:
            result = restore_ablbundle(filepath, pad_selected, pad_color)
            self.cleanup_upload(filepath)
            if result["success"]:
                # Add 1 to pad_selected for display since we subtracted 1 earlier
                result["message"] = result["message"].replace(f"pad ID {pad_selected}", f"pad ID {pad_selected + 1}")
                msets, ids = list_msets(return_free_ids=True)
                free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
                options = self.generate_pad_options(free_pads)
                color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
                first_free = free_pads[0] if free_pads else None
                pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
                return self.format_success_response(result["message"], options, pad_grid)
            else:
                # Regenerate available pad options on error
                msets, ids = list_msets(return_free_ids=True)
                free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
                options = self.generate_pad_options(free_pads)
                color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
                first_free = free_pads[0] if free_pads else None
                pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
                return self.format_error_response(result["message"], options=options, pad_grid=pad_grid, color_options=self.generate_color_options())
        except Exception as e:
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            first_free = free_pads[0] if free_pads else None
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map, first_free, "mset_index")
            return self.format_error_response(f"Error restoring bundle: {str(e)}", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())

    def generate_pad_options(self, free_pads):
        """
        Generates HTML <option> elements for available pads.
        
        Args:
            free_pads (list): List of available pad numbers.
        
        Returns:
            str: HTML-formatted options for a dropdown.
        """
        if not free_pads:
            return '<option value="" disabled>No pads available</option>'
        options = [f'<option value="{pad}" {"selected" if pad == free_pads[0] else ""}>{pad}</option>' for pad in free_pads]
        return ''.join(options)

    def format_success_response(self, message, options, pad_grid):
        return {
            "message": f"{message}",
            "options": options,
            "pad_grid": pad_grid,
        }

    def generate_pad_grid(self, used_ids, color_map, selected_pad=None, input_name="mset_index"):
        """Return HTML for a 32-pad grid showing occupied pads with colors.

        Args:
            used_ids (set): pad ids already occupied (0-indexed).
            color_map (dict): mapping of pad id to color id.
            selected_pad (int, optional): 1-based pad number to pre-select.
            input_name (str): name attribute for the radio inputs.
        """
        cells = []
        for row in range(4):
            for col in range(8):
                idx = (3 - row) * 8 + col
                num = idx + 1
                occupied = idx in used_ids
                status = 'occupied' if occupied else 'free'
                disabled = 'disabled' if occupied else ''
                checked = 'checked' if selected_pad and num == selected_pad and not occupied else ''
                color_id = color_map.get(idx)
                style = f' style="background-color: {rgb_string(color_id)}"' if color_id else ''
                label_text = "" if not occupied else ""
                cells.append(
                    f'<input type="radio" id="restore_pad_{num}" name="{input_name}" value="{num}" {checked} {disabled}>'
                    f'<label for="restore_pad_{num}" class="pad-cell {status}"{style}>{label_text}</label>'
                )
        grid_id = f'{input_name}_grid'
        return f'<div id="{grid_id}" class="pad-grid">' + ''.join(cells) + '</div>'

    def generate_color_options(self, input_name="mset_color", pad_input_name="mset_index"):
        """Return HTML for the custom color dropdown with pad preview."""
        colors = [PAD_COLORS[i] for i in sorted(PAD_COLORS)]
        names = [PAD_COLOR_LABELS[i] for i in sorted(PAD_COLOR_LABELS)]
        dropdown_id = f"{input_name}_dropdown"
        colors_json = json.dumps(colors)
        names_json = json.dumps(names)
        return (
            f'<div class="color-dropdown" id="{dropdown_id}">' \
            f'<div class="dropdown-toggle">' \
            f'<span class="preview-square"></span>' \
            f'<span class="preview-label"></span>' \
            f'<span class="arrow">&#9662;</span>' \
            f'</div>' \
            f'<div class="dropdown-menu"></div>' \
            f'<input type="hidden" name="{input_name}" value="1">' \
            f'</div>' \
            f'<script>' \
            f'const colors_{dropdown_id} = {colors_json};' \
            f'const names_{dropdown_id} = {names_json};' \
            f'(function() {{' \
            f' const c = colors_{dropdown_id};' \
            f' const n = names_{dropdown_id};' \
            f' const container = document.getElementById("{dropdown_id}");' \
            f' const toggle = container.querySelector(".dropdown-toggle");' \
            f' const menu = container.querySelector(".dropdown-menu");' \
            f' const hidden = container.querySelector("input");' \
            f' const padName = "{pad_input_name}";' \
            f' let open = false;' \
            f' let selected = parseInt(hidden.value) - 1;' \
            f' function render() {{' \
            f'  menu.innerHTML = "";' \
            f'  c.forEach((col, idx) => {{' \
            f'    const item = document.createElement("div");' \
            f'    item.className = "dropdown-item";' \
            f'    item.innerHTML = `<span class="preview-square" style="background-color: rgb(${{col[0]}}, ${{col[1]}}, ${{col[2]}});"></span> <span class="label">${{n[idx]}}</span>`;' \
            f'    item.addEventListener("click", () => {{selected = idx; hidden.value = idx + 1; update(); close();}});' \
            f'    menu.appendChild(item);' \
            f'  }});' \
            f' }}' \
            f' function previewPad() {{' \
            f'  const radios = document.querySelectorAll(`input[name="${{padName}}"]`);' \
            f'  radios.forEach(r => {{' \
            f'    const lab = document.querySelector(`label[for="${{r.id}}"]`);' \
            f'    if(lab && !r.checked && !r.disabled) lab.style.backgroundColor = "";' \
            f'  }});' \
            f'  const checked = document.querySelector(`input[name="${{padName}}"]:checked`);' \
            f'  if(checked) {{' \
            f'    const lab = document.querySelector(`label[for="${{checked.id}}"]`);' \
            f'    if(lab) {{ const col = c[selected]; lab.style.backgroundColor = `rgb(${{col[0]}}, ${{col[1]}}, ${{col[2]}})`; }}' \
            f'  }}' \
            f' }}' \
            f' function update() {{' \
            f'  const col = c[selected];' \
            f'  toggle.querySelector(".preview-square").style.backgroundColor = `rgb(${{col[0]}}, ${{col[1]}}, ${{col[2]}})`;'
            f'  toggle.querySelector(".preview-label").textContent = n[selected];' \
            f'  previewPad();' \
            f' }}' \
            f' function openMenu() {{ menu.style.display = "block"; open = true; }}' \
            f' function close() {{ menu.style.display = "none"; open = false; }}' \
            f' toggle.addEventListener("click", e => {{ e.stopPropagation(); open ? close() : openMenu(); }});' \
            f' document.addEventListener("click", e => {{ if (open && !container.contains(e.target)) close(); }});' \
            f' const grid = document.getElementById(`${{padName}}_grid`);' \
            f' if(grid) {{ grid.addEventListener("change", previewPad); grid.addEventListener("click", e => {{ if(e.target.tagName==="LABEL") previewPad(); }}); }}' \
            f' document.addEventListener("DOMContentLoaded", update);' \
            f' render(); update(); close();' \
            f'}})();' \
            f'</script>' \
            f'<style>' \
            f'.color-dropdown {{ position: relative; width: 200px; font-size: 0.875rem; }}' \
            f'.color-dropdown .dropdown-toggle {{ border: 1px solid #ddd; border-radius: 4px; padding: 0.5rem; cursor: pointer; display: flex; align-items: center; background: #fff; }}' \
            f'.color-dropdown .preview-square {{ width: 16px; height: 16px; margin-right: 8px; border: 1px solid #ccc; }}' \
            f'.color-dropdown .arrow {{ margin-left: auto; }}' \
            f'.color-dropdown .dropdown-menu {{ position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #ddd; border-radius: 4px; max-height: 200px; overflow-y: auto; z-index: 1000; }}' \
            f'.color-dropdown .dropdown-item {{ padding: 0.5rem; display: flex; align-items: center; cursor: pointer; }}' \
            f'.color-dropdown .dropdown-item:hover {{ background-color: #f0f0f0; }}' \
            f'.color-dropdown .dropdown-item .preview-square {{ margin-right: 8px; }}' \
            f'</style>'
        )
