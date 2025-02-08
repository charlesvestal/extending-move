# Move extra tools
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
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
            self.wfile.write(bytes(self.build_form(), "utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("404 Not Found", "utf-8"))

    def do_POST(self):
        if self.path == "/":
            content_type = self.headers.get('Content-Type')
            if not content_type:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: Content-Type header missing", "utf-8"))
                return

            # Initialize message variables
            message = ""
            message_type = ""  # "success" or "error"

            # Determine action based on the submit button pressed
            # To parse the form data correctly based on Content-Type
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
                self.respond_with_form(message, message_type)
                return

            if action == "slice":
                # Retrieve file
                if 'file' not in form:
                    message = "Bad Request: No file field in form."
                    message_type = "error"
                    self.respond_with_form(message, message_type)
                    return

                file_field = form['file']
                if not isinstance(file_field, cgi.FieldStorage):
                    message = "Bad Request: File field is not valid."
                    message_type = "error"
                    self.respond_with_form(message, message_type)
                    return

                if not file_field.filename:
                    message = "Bad Request: No file uploaded."
                    message_type = "error"
                    self.respond_with_form(message, message_type)
                    return

                filename = os.path.basename(file_field.filename)
                upload_dir = "uploads"
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                print(f"Saving uploaded file to {filepath}...")
                with open(filepath, "wb") as f:
                    shutil.copyfileobj(file_field.file, f)

                # Retrieve num_slices
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
                        self.respond_with_form(message, message_type)
                        return

                # Retrieve mode
                mode = "download"  # default
                if 'mode' in form:
                    mode_value = form.getvalue('mode')
                    if mode_value in ["download", "auto_place"]:
                        mode = mode_value
                    else:
                        message = "Bad Request: Invalid mode selected."
                        message_type = "error"
                        os.remove(filepath)  # Clean up uploaded file
                        self.respond_with_form(message, message_type)
                        return

                print(f"Processing kit generation with {num_slices} slices and mode '{mode}'...")
                # Process the uploaded WAV file
                try:
                    preset_name = os.path.splitext(filename)[0]
                    process_kit(filepath, preset_name=preset_name, num_slices=num_slices, keep_files=False, mode=mode)

                    if mode == "download":
                        bundle_filename = f"{preset_name}.ablpresetbundle"
                        bundle_path = os.path.join(os.getcwd(), bundle_filename)
                        
                        if os.path.exists(bundle_path):
                            print(f"Bundle created at {bundle_path}. Sending to client...")
                            with open(bundle_path, "rb") as f:
                                bundle_data = f.read()
                            
                            self.send_response(200)
                            self.send_header("Content-Type", "application/zip")
                            self.send_header("Content-Disposition", f"attachment; filename={bundle_filename}")
                            self.send_header("Content-Length", str(len(bundle_data)))
                            self.end_headers()
                            self.wfile.write(bundle_data)
                            
                            # Clean up uploaded file and bundle
                            os.remove(filepath)
                            os.remove(bundle_path)
                            print("Cleanup completed.")
                        else:
                            print("Failed to create bundle.")
                            message = "Failed to create bundle."
                            message_type = "error"
                            self.respond_with_form(message, message_type)
                    
                    elif mode == "auto_place":
                        preset_output_file = os.path.join("/data/UserData/UserLibrary/Track Presets", f"{preset_name}.ablpreset")
                        
                        # No need to check if preset exists; process_kit has already handled it.
                        # Respond with success message
                        print(f"Preset placed at {preset_output_file}.")

                        # Refresh the library after automatic placement
                        refresh_success, refresh_message = refresh_library()
                        if refresh_success:
                            combined_message = "Preset automatically placed successfully. " + refresh_message
                            combined_message_type = "success"
                        else:
                            combined_message = f"Preset automatically placed successfully, but failed to refresh library: {refresh_message}"
                            combined_message_type = "error"
                        
                        self.respond_with_form(combined_message, combined_message_type)
                        
                        # Clean up uploaded file
                        os.remove(filepath)
                        print("Uploaded file cleanup completed.")
                except Exception as e:
                    print(f"Error during kit processing: {e}")
                    message = f"Error processing kit: {e}"
                    message_type = "error"
                    self.respond_with_form(message, message_type)

            elif action == "refresh_library":
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
                    self.respond_with_form(message, message_type)
                except Exception as e:
                    print(f"Error during library refresh: {e}")
                    message = f"Error refreshing library: {e}"
                    message_type = "error"
                    self.respond_with_form(message, message_type)
            else:
                message = "Bad Request: Unknown action."
                message_type = "error"
                self.respond_with_form(message, message_type)

    def respond_with_form(self, message, message_type):
        """
        Sends back the form page with an inline message.
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html_content = self.build_form(message, message_type)
        self.wfile.write(bytes(html_content, "utf-8"))

    def build_form(self, message="", message_type=""):
        """
        Builds the HTML form with an optional message.
        """
        message_html = ""
        if message:
            if message_type == "success":
                message_html = f'<p style="color: green;">{message}</p>'
            elif message_type == "error":
                message_html = f'<p style="color: red;">{message}</p>'
        
        return f"""
            <html>
                <head>
                    <title>Upload WAV File</title>
                </head>
                <body>
                    <h2>Upload a WAV file to generate a kit</h2>
                    {message_html}
                    <form enctype="multipart/form-data" method="post">
                        <input type="hidden" name="action" value="slice"/>
                        <label for="file">Select WAV file:</label>
                        <input id="file" name="file" type="file" accept=".wav" required/>
                        <br/><br/>
                        <label for="num_slices">Number of slices (1-16):</label>
                        <input id="num_slices" name="num_slices" type="number" min="1" max="16" value="16" required/>
                        <br/><br/>
                        <label for="mode">Select Mode:</label>
                        <input type="radio" id="download" name="mode" value="download" checked>
                        <label for="download">Download .ablpreset</label>
                        <input type="radio" id="auto_place" name="mode" value="auto_place">
                        <label for="auto_place">Automatically place preset</label>
                        <br/><br/>
                        <input type="submit" name="action" value="slice"/>
                    </form>
                    <hr/>
                    <form method="post">
                        <input type="hidden" name="action" value="refresh_library"/>
                        <input type="submit" value="Refresh Library"/>
                    </form>
                </body>
            </html>
        """

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
