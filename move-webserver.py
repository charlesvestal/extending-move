# Move extra tools
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import shutil
from urllib.parse import parse_qs
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
                            <input type="submit" value="Upload"/>
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
            content_length = int(self.headers['Content-Length'])
            content_type = self.headers['Content-Type']

            if not content_type.startswith("multipart/form-data"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: Expected multipart/form-data", "utf-8"))
                return

            boundary = content_type.split("boundary=")[1].encode()
            remainbytes = content_length
            fields = {}
            files = {}

            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if boundary in line:
                    # Read Content-Disposition
                    disposition = self.rfile.readline()
                    remainbytes -= len(disposition)
                    disposition = disposition.decode()
                    # Get field name
                    if 'filename="' in disposition:
                        # It's a file
                        filename = disposition.split('filename="')[1].split('"')[0]
                        filepath = os.path.join("uploads", filename)
                        os.makedirs("uploads", exist_ok=True)

                        # Skip Content-Type line
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        # Skip empty line
                        line = self.rfile.readline()
                        remainbytes -= len(line)

                        # Read the file
                        try:
                            with open(filepath, "wb") as out_file:
                                preline = self.rfile.readline()
                                remainbytes -= len(preline)
                                while remainbytes > 0:
                                    line = self.rfile.readline()
                                    remainbytes -= len(line)
                                    if boundary in line:
                                        preline = preline.rstrip(b'\r\n')
                                        out_file.write(preline)
                                        break
                                    else:
                                        out_file.write(preline)
                                        preline = line
                            files['file'] = filepath
                        except Exception as e:
                            self.send_response(500)
                            self.end_headers()
                            self.wfile.write(bytes(f"Failed to write file: {e}", "utf-8"))
                            return
                    else:
                        # It's a form field
                        field_name = disposition.split('name="')[1].split('"')[0]
                        # Skip Content-Type line if exists
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        if line.strip().startswith(b'Content-Type'):
                            # Read and skip Content-Type line
                            line = self.rfile.readline()
                            remainbytes -= len(line)
                        # Skip empty line
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        # Read the field value
                        value = b''
                        while True:
                            line = self.rfile.readline()
                            remainbytes -= len(line)
                            if boundary in line:
                                value = value.rstrip(b'\r\n')
                                break
                            else:
                                value += line
                        fields[field_name] = value.decode()

            # Check if file was uploaded
            if 'file' not in files:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Bad Request: No file uploaded", "utf-8"))
                return

            # Get num_slices
            num_slices = 16  # default
            if 'num_slices' in fields:
                try:
                    num_slices = int(fields['num_slices'])
                    if not (1 <= num_slices <= 16):
                        raise ValueError
                except ValueError:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(bytes("Bad Request: Number of slices must be an integer between 1 and 16", "utf-8"))
                    return

            # Process the uploaded WAV file
            try:
                preset_name = os.path.splitext(os.path.basename(files['file']))[0]
                process_kit(files['file'], preset_name=preset_name, num_slices=num_slices, keep_files=False)
                bundle_filename = f"{preset_name}.ablpresetbundle"
                bundle_path = os.path.join(os.getcwd(), bundle_filename)
                
                if os.path.exists(bundle_path):
                    with open(bundle_path, "rb") as f:
                        bundle_data = f.read()
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", f"attachment; filename={bundle_filename}")
                    self.send_header("Content-Length", str(len(bundle_data)))
                    self.end_headers()
                    self.wfile.write(bundle_data)
                    
                    # Clean up uploaded file and bundle
                    os.remove(files['file'])
                    os.remove(bundle_path)
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(bytes("Failed to create bundle.", "utf-8"))
            except Exception as e:
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
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
