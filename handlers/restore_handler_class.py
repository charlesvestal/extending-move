import os
import logging
from handlers.base_handler import BaseHandler
from core.list_msets_handler import list_msets
from core.restore_handler import restore_ablbundle
from core.pad_colors import PAD_COLORS, rgb_string

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
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
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
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
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
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
            return self.format_error_response("Invalid pad selection provided.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())
        # Early validation: color
        if not pad_color or not pad_color.isdigit():
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
            return self.format_error_response("Invalid pad color provided.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())

        pad_selected = int(pad_selected) - 1  # Convert back to internal ID
        pad_color = int(pad_color)

        if not (0 <= pad_selected <= 31):
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
            return self.format_error_response("Invalid pad selection. Must be between 1 and 32.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())
        if not (1 <= pad_color <= 25):
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
            return self.format_error_response("Invalid pad color. Must be between 1 and 25.", options=options, pad_grid=pad_grid, color_options=self.generate_color_options())

        success, filepath, error_response = self.handle_file_upload(form, "ablbundle")
        if not success:
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
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
                pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
                return self.format_success_response(result["message"], options, pad_grid)
            else:
                # Regenerate available pad options on error
                msets, ids = list_msets(return_free_ids=True)
                free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
                options = self.generate_pad_options(free_pads)
                color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
                pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
                return self.format_error_response(result["message"], options=options, pad_grid=pad_grid, color_options=self.generate_color_options())
        except Exception as e:
            msets, ids = list_msets(return_free_ids=True)
            free_pads = sorted([pad_id + 1 for pad_id in ids.get("free", [])])
            options = self.generate_pad_options(free_pads)
            color_map = {int(m["mset_id"]): int(m["mset_color"]) for m in msets if str(m["mset_color"]).isdigit()}
            pad_grid = self.generate_pad_grid(ids.get("used", set()), color_map)
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

    def generate_pad_grid(self, used_ids, color_map):
        """Return HTML for a 32-pad grid showing occupied pads with colors."""
        cells = []
        for row in range(4):
            for col in range(8):
                idx = (3 - row) * 8 + col
                num = idx + 1
                occupied = idx in used_ids
                status = 'occupied' if occupied else 'free'
                disabled = 'disabled' if occupied else ''
                color_id = color_map.get(idx)
                style = f' style="background-color: {rgb_string(color_id)}"' if color_id else ''
                label_text = "" if not occupied else ""
                cells.append(
                    f'<input type="radio" id="restore_pad_{num}" name="mset_index" value="{num}" {disabled}>'
                    f'<label for="restore_pad_{num}" class="pad-cell {status}"{style}>{label_text}</label>'
                )
        return '<div class="pad-grid">' + ''.join(cells) + '</div>'

    def generate_color_options(self):
        options = ['<option value="" disabled selected>-- Select Color --</option>']
        for i in range(1, 26):
            rgb = rgb_string(i)
            options.append(
                f'<option value="{i}" style="background-color: {rgb};">&#9632; {i}</option>'
            )
        return ''.join(options)
