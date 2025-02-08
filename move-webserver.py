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
                            <input name="file" type="file" accept=".wav"/>
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
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary not in line:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Content does not start with boundary", "utf-8"))
                return

            line = self.rfile.readline()
            remainbytes -= len(line)
            disposition = line.decode()
            if 'filename="' not in disposition:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(bytes("Can't find out file name...", "utf-8"))
                return
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
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(bytes(f"Failed to write file: {e}", "utf-8"))
                return

            # Process the uploaded WAV file
            try:
                preset_name = os.path.splitext(filename)[0]
                process_kit(filepath, preset_name=preset_name, num_slices=16, keep_files=False)
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
                    os.remove(filepath)
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
