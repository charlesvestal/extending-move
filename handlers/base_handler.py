#!/usr/bin/env python3
import html
import os
import shutil
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple, Set
from core.pad_colors import rgb_string

logger = logging.getLogger(__name__)

class BaseHandler:
    """
    Base class for all feature handlers in the Move webserver.
    
    This class provides common functionality for handling web requests, including:
    - File upload handling with temporary storage
    - Form action validation
    - Response formatting
    - Cleanup of temporary files
    - Shared pad grid generation for set selection UI
    
    Each feature handler should inherit from this class and implement
    its own handle_post method to process specific feature requests.
    """

    def generate_pad_grid(
        self,
        used_ids: Set[int],
        color_map: Optional[Dict[int, int]] = None,
        name_map: Optional[Dict[int, str]] = None,
        bpm_map: Optional[Dict[int, str]] = None,
        selected_idx: Optional[int] = None,
        active_idx: Optional[int] = None,
        input_name: str = "pad_index",
        free_only: bool = False,
        view_only: bool = False,
    ) -> str:
        """Generate HTML for a 32-pad grid showing set occupancy with colors, names, and BPM.

        This is the standard pad grid implementation shared across all handlers
        that need pad selection (Restore, Set Inspector, MIDI Upload, etc.).
        Displays pad number, set name, and BPM inside each pad like the Overview page.

        Args:
            used_ids: Set of pad indices (0-31) that contain sets.
            color_map: Optional mapping of pad index to pad color ID (1-25).
            name_map: Optional mapping of pad index to set name.
            bpm_map: Optional mapping of pad index to BPM string.
            selected_idx: Optional pad index to mark as pre-selected.
            input_name: Name attribute for the radio inputs (default: "pad_index").
            free_only: If True, only free pads are selectable (for restore/upload).
                         If False, only occupied pads are selectable (for set inspector).

        Returns:
            HTML string containing the pad grid div with styled radio inputs.
        """
        color_map = color_map or {}
        name_map = name_map or {}
        bpm_map = bpm_map or {}
        cells = []
        for row in range(4):
            for col in range(8):
                idx = (3 - row) * 8 + col
                num = idx + 1
                has_set = idx in used_ids

                if free_only:
                    # For restore/upload: only free pads selectable
                    disabled = "disabled" if has_set else ""
                else:
                    # For set inspector: only occupied pads selectable
                    disabled = "" if has_set else "disabled"

                status = "occupied" if has_set else "free"
                active = " active" if active_idx is not None and idx == active_idx else ""
                checked = " checked" if selected_idx is not None and idx == selected_idx else ""
                color_id = color_map.get(idx)
                # Generate semi-transparent background + solid border like Overview page
                if color_id:
                    rgb = rgb_string(color_id).replace("rgb(", "").replace(")", "")
                    style = f' style="background-color: rgba({rgb}, 0.2); border-color: rgb({rgb});"'
                else:
                    style = ""
                name = html.escape(str(name_map.get(idx, "")))
                bpm = html.escape(str(bpm_map.get(idx, "")))

                # Build inner content like Overview page
                if has_set:
                    inner_html = f'<div class="pad-num">{num}</div><div class="pad-name">{name}</div>'
                    if bpm:
                        inner_html += f'<div class="pad-bpm">{bpm} BPM</div>'
                else:
                    inner_html = f'<div class="pad-num">{num}</div>'

                cells.append(
                    f'<input type="radio" id="pad_{num}" name="{input_name}" value="{num}"{checked} {disabled}>'
                    f'<label for="pad_{num}" class="pad-cell {status}{active}"{style}>{inner_html}</label>'
                )
        grid_class = "pad-grid view-only" if view_only else "pad-grid"
        return f'<div class="{grid_class}">' + "".join(cells) + "</div>"

    def __init__(self):
        """
        Initialize the handler with a temporary uploads directory.
        Uses absolute path to prevent directory location issues.
        Creates the directory if it doesn't exist.
        """
        self.upload_dir = os.path.abspath("uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_action(self, form, expected_action: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Validate that the form's action field matches the expected action.
        
        Args:
            form: The form data from the request
            expected_action: The action string that should be in the form
        
        Returns:
            tuple: (is_valid, error_response)
            - is_valid: True if action is valid, False otherwise
            - error_response: None if valid, error response dict if invalid
        """
        action = form.getvalue('action')
        if action != expected_action:
            return False, {"message": f"Bad Request: Invalid action '{action}'", "message_type": "error"}
        return True, None

    def handle_file_upload(self, form, field_name: str = 'file') -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
        """
        Handle file upload from a multipart form.
        Saves the uploaded file to a temporary directory.
        
        Args:
            form: The form data from the request
            field_name: Name of the file field in the form (default: 'file')
        
        Returns:
            tuple: (success, filepath, error_response)
            - success: True if upload succeeded, False otherwise
            - filepath: Path to saved file if successful, None otherwise
            - error_response: Error response dict if failed, None if successful
        
        The caller is responsible for cleaning up the uploaded file
        by calling cleanup_upload() when the file is no longer needed.
        """
        if field_name not in form:
            return False, None, {"message": f"Bad Request: No {field_name} field in form", "message_type": "error"}

        file_field = form[field_name]
        if not hasattr(file_field, "filename") or not file_field.filename:
            return False, None, {"message": f"Bad Request: Invalid {field_name}", "message_type": "error"}

        try:
            filename = os.path.basename(file_field.filename)
            # Use a unique temp name to avoid collisions between concurrent uploads
            fd, filepath = tempfile.mkstemp(
                suffix=os.path.splitext(filename)[1],
                dir=self.upload_dir,
            )
            os.close(fd)
            
            # Save the file
            with open(filepath, "wb") as f:
                shutil.copyfileobj(file_field.file, f)
            
            if not os.path.exists(filepath):
                return False, None, {"message": "File upload failed: File not saved", "message_type": "error"}
            
            return True, filepath, None
        except Exception as e:
            return False, None, {"message": f"Error saving uploaded file: {str(e)}", "message_type": "error"}

    def save_uploaded_file(self, file_item) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
        """
        Save a single uploaded file item to a temporary directory.
        
        Args:
            file_item: The file item from the form (has .filename and .file attributes)
        
        Returns:
            tuple: (success, filepath, error_response)
            - success: True if upload succeeded, False otherwise
            - filepath: Path to saved file if successful, None otherwise
            - error_response: Error response dict if failed, None if successful
        
        The caller is responsible for cleaning up the uploaded file
        by calling cleanup_upload() when the file is no longer needed.
        """
        if not hasattr(file_item, "filename") or not file_item.filename:
            return False, None, {"message": "Bad Request: Invalid file item", "message_type": "error"}

        try:
            filename = os.path.basename(file_item.filename)
            # Use a unique temp name to avoid collisions between concurrent uploads
            # with the same basename (e.g. two files named clip.mid)
            fd, filepath = tempfile.mkstemp(
                suffix=os.path.splitext(filename)[1],
                dir=self.upload_dir,
            )
            os.close(fd)
            
            # Save the file
            with open(filepath, "wb") as f:
                shutil.copyfileobj(file_item.file, f)
            
            if not os.path.exists(filepath):
                return False, None, {"message": "File upload failed: File not saved", "message_type": "error"}
            
            return True, filepath, None
        except Exception as e:
            return False, None, {"message": f"Error saving uploaded file: {str(e)}", "message_type": "error"}

    def format_success_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Format a success response with optional additional data.
        
        Args:
            message: Success message to display
            **kwargs: Additional key-value pairs to include in response
        
        Returns:
            dict: Response dictionary with message and success type,
                 plus any additional provided data
        """
        response = {
            "message": message,
            "message_type": "success"
        }
        response.update(kwargs)
        return response

    def format_error_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Format an error response with optional additional data.
        
        Args:
            message: Error message to display
            **kwargs: Additional key-value pairs to include in response
        
        Returns:
            dict: Response dictionary with message and error type,
                 plus any additional provided data
        """
        response = {
            "message": message,
            "message_type": "error"
        }
        response.update(kwargs)
        return response

    def format_info_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """Format an informational response."""
        response = {
            "message": message,
            "message_type": "info"
        }
        response.update(kwargs)
        return response

    def cleanup_upload(self, filepath: str):
        """
        Clean up an uploaded file.
        Should be called after processing is complete or if an error occurs.
        
        Args:
            filepath: Path to the file to remove
        
        Note:
            Silently ignores missing files and logs cleanup failures
            to avoid interrupting the response flow.
        """
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.warning("Failed to clean up uploaded file %s: %s", filepath, e)


    def format_json_response(self, data, status=200):
        """
        Format a JSON response for AJAX handlers.
        Args:
            data: dict to encode as JSON
            status: HTTP status code
        Returns:
            dict with status, headers, and content (JSON-encoded string)
        """
        import json
        return {
            "status": status,
            "headers": [("Content-Type", "application/json")],
            "content": json.dumps(data)
        }
