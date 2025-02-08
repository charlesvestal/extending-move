# Move extra tools
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import shutil
import cgi
from kit_handler import process_kit
from refresh_handler import refresh_library
from reverse_handler import get_wav_files, reverse_wav_file

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
        elif self.path == "/reverse":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            wav_files = get_wav_files()
            # Render reverse.html with the list of wav_files
            try:
                with open(os.path.join("templates", "reverse.html"), "r") as f:
                    template = f.read()
                # Simple templating to insert wav_files into the select options
                options = ''.join([f'<option value="{file}">{file}</option>' for file in wav_files])
                html_content = template.replace("{% for file in wav_files %}", "").replace("{% endfor %}", "")
                html_content = template.replace("{{ file }}", "{file}")  # Placeholder
                # Since simple replacement is used, loop is manually handled
                options_html = ''.join([f'<option value="{file}">{file}</option>' for file in wav_files])
                html_content = template.replace("{% for file in wav_files %}", "").replace("{{ file }}", "{}").format(*(files for files in wav_files))
                # Properly replace the select options
                html_content = f"""<html>
    <head>
        <title>Reverse WAV</title>
        <link rel="stylesheet" href="/style.css">
    </head>
    <body>
        <h2>Reverse a WAV File</h2>
        {self.message_html if hasattr(self, 'message_html') else ''}
        <form method="post">
            <input type="hidden" name="action" value="reverse_file"/>
            
            <label for="wav_file">Select WAV file to reverse:</label>
            <select id="wav_file" name="wav_file" required>
                <option value="" disabled selected>--Select a WAV file--</option>
                {options}
            </select>
            <br/><br/>
            
            <button type="submit" onclick="confirmOverwrite()">Reverse and Overwrite</button>
        </form>
        
        <script>
            function confirmOverwrite() {{
                const wavFileSelect = document.getElementById('wav_file');
                const selectedFile = wavFileSelect.value;
                if (!selectedFile) {{
                    alert('Please select a WAV file to reverse.');
                    event.preventDefault();
                    return;
                }}
                const confirmAction = confirm(`Are you sure you want to overwrite "${{selectedFile}}" with its reversed version?`);
                if (!confirmAction) {{
                    event.preventDefault();
                }}
            }}
        </script>
    </body>
</html>"""
                self.wfile.write(bytes(html_content, "utf-8"))
            except Exception as e:
                error_message = f"Error rendering reverse.html: {e}"
                self.send_response(500)
                self.end_headers()
                self.wfile.write(bytes(f"<html><body><p style='color: red;'>{error_message}</p></body></html>", "utf-8"))
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
        if self.path in ["/slice", "/refresh", "/reverse"]:
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

            elif action == "reverse_file" and self.path == "/reverse":
                print("Processing reverse WAV file request...")
                try:
                    wav_file = form.getvalue('wav_file')
                    if not wav_file:
                        message = "Bad Request: No WAV file selected."
                        message_type = "error"
                        self.respond_with_form(self.path, message, message_type)
                        return

                    # Path is fixed to /data/UserData/UserLibrary/Samples
                    directory = "/data/UserData/UserLibrary/Samples"
                    if not os.path.isdir(directory):
                        message = f"Server Error: Directory does not exist: {directory}"
                        message_type = "error"
                        self.respond_with_form(self.path, message, message_type)
                        return

                    success, msg = reverse_wav_file(wav_file, directory=directory)
                    if success:
                        message = msg
                        message_type = "success"
                    else:
                        message = msg
                        message_type = "error"

                    self.respond_with_form(self.path, message, message_type)
                except Exception as e:
                    self.respond_with_form(self.path, f"Error processing reverse WAV file: {e}", "error")

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
        elif path == "/reverse":
            template_file = "reverse.html"
        else:
            # Default to index.html if path is unrecognized
            template_file = "index.html"

        # Read the form template
        template_path = os.path.join("templates", template_file)
        if not os.path.exists(template_path):
            # Fallback to a simple message if template does not exist
            self.wfile.write(bytes(f"<html><body><p>{message}</p></body></html>", "utf-8"))
            return

        try:
            with open(template_path, "r") as f:
                html_content = f.read()
        except Exception as e:
            error_message = f"Error reading template file: {e}"
            self.send_response(500)
            self.end_headers()
            self.wfile.write(bytes(f"<html><body><p style='color: red;'>{error_message}</p></body></html>", "utf-8"))
            return

        # Insert the message_html
        if "{message_html}" in html_content:
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
