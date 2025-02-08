# Move extra tools
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import shutil
import cgi
from kit_handler import process_kit, refresh_library

hostName = "0.0.0.0"
serverPort = 666

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(os.path.join("templates", "index.html"), "r") as f:
                self.wfile.write(bytes(f.read(), "utf-8"))
        elif self.path == "/slice":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(os.path.join("templates", "slice.html"), "r") as f:
                html_content = f.read().replace("{message_html}", "")
                self.wfile.write(bytes(html_content, "utf-8"))
        elif self.path == "/refresh":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(os.path.join("templates", "refresh.html"), "r") as f:
                html_content = f.read().replace("{message_html}", "")
                self.wfile.write(bytes(html_content, "utf-8"))
        elif self.path == "/style.css":
            self.send_response(200)
            self.send_header("Content-type", "text/css")
            self.end_headers()
            with open(os.path.join("templates", "style.css"), "r") as f:
                self.wfile.write(bytes(f.read(), "utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("404 Not Found", "utf-8"))

    def do_POST(self):
        if self.path in ["/slice", "/refresh"]:
            content_type = self.headers.get('Content-Type')
            if not content_type:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: Content-Type header missing", "utf-8"))
                return

            # Initialize message variables
            message = ""
            message_type = ""  # "success" or "error"

            # Determine action based on the action field
            try:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={
                        'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': content_type,
                    }
                )
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes(f"Bad Request: {e}", "utf-8"))
                return

            action = form.getvalue('action')
            if not action:
                message = "Bad Request: No action specified."
                message_type = "error"
                self.respond_with_form(self.path, message, message_type)
                return

            mode = form.getvalue('mode') if 'mode' in form else None

            if action == "slice" and self.path == "/slice":
                if not mode:
                    message = "Bad Request: No mode specified."
                    message_type = "error"
                    self.respond_with_form(self.path, message, message_type)
                    return

                if mode not in ["download", "auto_place"]:
                    message = "Bad Request: Invalid mode selected."
                    message_type = "error"
                    self.respond_with_form(self.path, message, message_type)
                    return

                # Process the kit
                try:
                    # Retrieve and save the uploaded file
                    if 'file' not in form:
                        message = "Bad Request: No file field in form."
                        message_type = "error"
                        self.respond_with_form(self.path, message, message_type)
                        return

                    file_field = form['file']
                    if not isinstance(file_field, cgi.FieldStorage):
                        message = "Bad Request: File field is not valid."
                        message_type = "error"
                        self.respond_with_form(self.path, message, message_type)
                        return

                    if not file_field.filename:
                        message = "Bad Request: No file uploaded."
                        message_type = "error"
                        self.respond_with_form(self.path, message, message_type)
                        return

                    filename = os.path.basename(file_field.filename)
                    upload_dir = "uploads"
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, filename)
                    print(f"Saving uploaded file to {filepath}...")
                    with open(filepath, "wb") as f:
                        shutil.copyfileobj(file_field.file, f)

                    preset_name = os.path.splitext(filename)[0]

                    num_slices = 16  # default
                    if 'num_slices' in form:
                        try:
                            num_slices = int(form.getvalue('num_slices'))
                            if not (1 <= num_slices <= 16):
                                raise ValueError
                        except ValueError:
                            message = "Bad Request: Number of slices must be an integer between 1 and 16."
                            message_type = "error"
                            os.remove(filepath)  # Clean up uploaded file
                            self.respond_with_form(self.path, message, message_type)
                            return

                    # Start of new code to handle regions
                    regions = None
                    if 'regions' in form:
                        regions_str = form.getvalue('regions')
                        try:
                            regions = json.loads(regions_str)
                            print(f"Received regions: {regions}")
                        except json.JSONDecodeError:
                            message = "Invalid regions format. Regions should be a valid JSON."
                            message_type = "error"
                            os.remove(filepath)  # Clean up uploaded file
                            self.respond_with_form(self.path, message, message_type)
                            return
                    # End of new code

                    if regions:
                        num_slices = None  # Optionally disable num_slices if regions are used

                    print(f"Processing kit generation with {num_slices} slices and mode '{mode}'...")
                    # Process the uploaded WAV file
                    result = process_kit(
                        input_wav=filepath,
                        preset_name=preset_name,
                        regions=regions,           # Pass regions here
                        num_slices=num_slices, 
                        keep_files=False,
                        mode=mode
                    )

                    if mode == "download":
                        if result.get('success'):
                            bundle_path = result.get('bundle_path')
                            if os.path.exists(bundle_path):
                                print(f"Bundle created at {bundle_path}. Sending to client...")
                                with open(bundle_path, "rb") as f:
                                    bundle_data = f.read()

                                self.send_response(200)
                                self.send_header("Content-Type", "application/zip")
                                self.send_header("Content-Disposition", f"attachment; filename={os.path.basename(bundle_path)}")
                                self.send_header("Content-Length", str(len(bundle_data)))
                                self.end_headers()
                                self.wfile.write(bundle_data)

                                # Clean up bundle
                                os.remove(bundle_path)
                                print("Cleanup completed.")
                            else:
                                print("Failed to create bundle.")
                                message = "Failed to create bundle."
                                message_type = "error"
                                self.respond_with_form(self.path, message, message_type)
                        else:
                            self.respond_with_form(self.path, result.get('message', 'An error occurred.'), "error")
                    elif mode == "auto_place":
                        if result.get('success'):
                            self.respond_with_form(self.path, result.get('message', 'Preset placed successfully.'), "success")
                        else:
                            self.respond_with_form(self.path, result.get('message', 'An error occurred.'), "error")
                except Exception as e:
                    self.respond_with_form(self.path, f"Error processing kit: {e}", "error")

            elif action == "refresh_library" and self.path == "/refresh":
                print("Refreshing library...")
                # Ensure no file upload is required for this action
                try:
                    success, refresh_message = refresh_library()
                    if success:
                        message = refresh_message
                        message_type = "success"
                    else:
                        message = refresh_message
                        message_type = "error"
                    self.respond_with_form(self.path, message, message_type)
                except Exception as e:
                    print(f"Error during library refresh: {e}")
                    message = f"Error refreshing library: {e}"
                    message_type = "error"
                    self.respond_with_form(self.path, message, message_type)
            else:
                message = "Bad Request: Unknown action or incorrect path."
                message_type = "error"
                self.respond_with_form(self.path, message, message_type)

    def respond_with_form(self, path, message, message_type):
        """
        Sends back the appropriate form page with an inline message.
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if path == "/slice":
            template_file = "slice.html"
        elif path == "/refresh":
            template_file = "refresh.html"
        else:
            # Default to index.html if path is unrecognized
            template_file = "index.html"

        # Read the form template
        template_path = os.path.join("templates", template_file)
        if not os.path.exists(template_path):
            # Fallback to a simple message if template does not exist
            self.wfile.write(bytes(f"<html><body><p>{message}</p></body></html>", "utf-8"))
            return

        with open(template_path, "r") as f:
            html_content = f.read()

        # Replace placeholder with message_html
        if message:
            if message_type == "success":
                message_html = f'<p style="color: green;">{message}</p>'
            elif message_type == "error":
                message_html = f'<p style="color: red;">{message}</p>'
            else:
                message_html = f'<p>{message}</p>'
            html_content = html_content.replace("{message_html}", message_html)
        else:
            html_content = html_content.replace("{message_html}", "")

        self.wfile.write(bytes(html_content, "utf-8"))

if __name__ == "__main__":
    print("Starting webserver")
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print(f"Server started http://{hostName}:{serverPort}")
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")
