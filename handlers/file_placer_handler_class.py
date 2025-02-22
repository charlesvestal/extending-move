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
        elif mode == "place" or not mode:
            # Handle non-zip file placement: simply place the uploaded file at the specified destination
            success, file_path, err = self.handle_file_upload(form, "file")
            if not success:
                return self.format_error_response("Failed to upload file.")
            dest_dir = form.getvalue("destination")
            if not dest_dir:
                self.cleanup_upload(file_path)
                return self.format_error_response("No destination directory provided.")
            # Retrieve the original filename from the file field
            file_field = form["file"]
            filename = os.path.basename(file_field.filename) if file_field.filename else os.path.basename(file_path)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, filename)
            try:
                shutil.move(file_path, dest_path)
            except Exception as e:
                return self.format_error_response(f"Error placing file: {e}")
            return self.format_success_response("File placed successfully.")
        else:
            return self.format_error_response("Unsupported mode.")
