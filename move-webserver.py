# Move extra tools
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import shutil
import cgi
from kit_handler import process_kit

hostName = "0.0.0.0"
serverPort = 666

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("""
                <html>
                    <head>
                        <title>Upload WAV File</title>
                    </head>
                    <body>
                        <h2>Upload a WAV file to generate a kit</h2>
                        <form enctype="multipart/form-data" method="post">
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
                            <input type="submit" value="Slice"/>
                        </form>
                    </body>
                </html>
            """, "utf-8"))
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

            ctype, pdict = cgi.parse_header(content_type)
            if ctype != 'multipart/form-data':
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: Expected multipart/form-data", "utf-8"))
                return

            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            pdict['CONTENT-LENGTH'] = int(self.headers.get('Content-Length'))
            print("Parsing multipart form data...")
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
            })

            # Retrieve file
            if 'file' not in form:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: No file field in form", "utf-8"))
                return

            file_field = form['file']
            if not isinstance(file_field, cgi.FieldStorage):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: File field is not valid", "utf-8"))
                return

            if not file_field.filename:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: No file uploaded", "utf-8"))
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
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(bytes("Bad Request: Number of slices must be an integer between 1 and 16", "utf-8"))
                    os.remove(filepath)  # Clean up uploaded file
                    return

            # Retrieve mode
            mode = "download"  # default
            if 'mode' in form:
                mode_value = form.getvalue('mode')
                if mode_value in ["download", "auto_place"]:
                    mode = mode_value
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(bytes("Bad Request: Invalid mode selected", "utf-8"))
                    os.remove(filepath)  # Clean up uploaded file
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
                        self.send_response(500)
                        self.end_headers()
                        self.wfile.write(bytes("Failed to create bundle.", "utf-8"))
                
                elif mode == "auto_place":
                    preset_output_file = os.path.join("/data/UserData/UserLibrary/Track Presets", f"{preset_name}.ablpreset")
                    
                    # No need to check if preset exists; process_kit has already handled it.
                    # Respond with success message
                    print(f"Preset placed at {preset_output_file}.")
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(bytes("Preset automatically placed successfully.", "utf-8"))
                    
                    # Clean up uploaded file
                    os.remove(filepath)
                    print("Uploaded file cleanup completed.")
            except Exception as e:
                print(f"Error during kit processing: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(bytes(f"Error processing kit: {e}", "utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("404 Not Found", "utf-8"))

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
