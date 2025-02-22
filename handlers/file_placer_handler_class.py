from handlers.base_handler import BaseHandler
import os
import zipfile
import shutil
import json
import cgi

class FilePlacerHandler(BaseHandler):
    def handle_post(self, form: cgi.FieldStorage):
        mode = form.getvalue("mode")
        if mode == "zip":
            # Handle a zip file upload
            success, zip_path, err = self.handle_file_upload(form, "file")
            if not success:
                return self.format_error_response("Failed to upload zip file.")
            dest_dir = form.getvalue("destination")
            if not dest_dir:
                self.cleanup_upload(zip_path)
                return self.format_error_response("No destination directory provided.")
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(dest_dir)
            except Exception as e:
                self.cleanup_upload(zip_path)
                return self.format_error_response(f"Error extracting zip file: {e}")
            self.cleanup_upload(zip_path)
            return self.format_success_response("Zip file extracted successfully.")
        else:
            return self.format_error_response("Only zip mode is supported.")
