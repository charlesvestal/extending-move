#!/usr/bin/env python3
# Move extra tools
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import shutil
import cgi
from kit_handler import process_kit
from refresh_handler import refresh_library
from reverse_handler import get_wav_files, reverse_wav_file

# Additional imports for PID management
import atexit
import signal
import sys
import time

BASE_SAMPLES_DIR = "/data/UserData/UserLibrary/Samples"
PID_FILE = os.path.expanduser('~/extending-move/move-webserver.pid')

class TemplateManager:
    def __init__(self, template_dir="templates"):
        self.template_dir = template_dir
        self.templates = {}

    def get_template(self, template_name):
        if template_name not in self.templates:
            path = os.path.join(self.template_dir, template_name)
            with open(path, "r") as f:
                self.templates[template_name] = f.read()
        return self.templates[template_name]

    def render(self, template_name, **kwargs):
        template = self.get_template(template_name)
        # Handle special cases
        if template_name == "reverse.html":
            kwargs["options"] = generate_wav_options(BASE_SAMPLES_DIR)
            template = template.replace("{{ options }}", kwargs["options"])
        
        # Handle message display
        message = kwargs.get("message", "")
        message_type = kwargs.get("message_type", "")
        if message:
            if message_type == "success":
                message_html = f'<p style="color: green;">{message}</p>'
            elif message_type == "error":
                message_html = f'<p style="color: red;">{message}</p>'
            else:
                message_html = f'<p>{message}</p>'
        else:
            message_html = ""
        template = template.replace("{message_html}", message_html)
        
        return template

class RouteHandler:
    def __init__(self):
        self.get_routes = {}
        self.post_routes = {}
        self.template_manager = TemplateManager()

    def get(self, path, template_name=None, content_type="text/html"):
        def decorator(handler):
            self.get_routes[path] = {
                "handler": handler,
                "template": template_name,
                "content_type": content_type
            }
            return handler
        return decorator

    def post(self, path):
        def decorator(handler):
            self.post_routes[path] = handler
            return handler
        return decorator

def write_pid():
    """Write the current process PID to the PID_FILE."""
    pid = os.getpid()
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(pid))
        print(f"PID {pid} written to {PID_FILE}")
    except Exception as e:
        print(f"Error writing PID file: {e}")

def remove_pid():
    """Remove the PID file."""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print(f"PID file {PID_FILE} removed.")
    except Exception as e:
        print(f"Error removing PID file: {e}")

def handle_exit(signum, frame):
    """Handle termination signals gracefully."""
    print(f"Received signal {signum}, exiting gracefully.")
    sys.exit(0)

def generate_wav_options(directory):
    """Generates HTML <option> elements for each WAV file in the directory."""
    wav_files = get_wav_files(directory)
    return ''.join([f'<option value="{file}">{file}</option>' for file in wav_files])

class MyServer(BaseHTTPRequestHandler):
    route_handler = RouteHandler()

    @route_handler.get("/", "index.html")
    def handle_index(self):
        return {}

    @route_handler.get("/slice", "slice.html")
    def handle_slice_get(self):
        return {}

    @route_handler.get("/refresh", "refresh.html")
    def handle_refresh_get(self):
        return {}

    @route_handler.get("/reverse", "reverse.html")
    def handle_reverse_get(self):
        return {}

    @route_handler.get("/style.css", "style.css", "text/css")
    def handle_css(self):
        return {}

    def do_GET(self):
        route = self.route_handler.get_routes.get(self.path)
        if route:
            try:
                handler_result = route["handler"](self)
                if route["template"]:
                    content = self.route_handler.template_manager.render(
                        route["template"],
                        **handler_result
                    )
                    self.send_response(200)
                    self.send_header("Content-type", route["content_type"])
                    self.end_headers()
                    self.wfile.write(bytes(content, "utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(bytes("404 Not Found", "utf-8"))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    @route_handler.post("/slice")
    def handle_slice_post(self, form):
        action = form.getvalue('action')
        if action != "slice":
            return {"message": "Bad Request: Invalid action", "message_type": "error"}

        mode = form.getvalue('mode')
        if not mode or mode not in ["download", "auto_place"]:
            return {"message": "Bad Request: Invalid mode", "message_type": "error"}

        if 'file' not in form:
            return {"message": "Bad Request: No file field in form", "message_type": "error"}

        file_field = form['file']
        if not isinstance(file_field, cgi.FieldStorage) or not file_field.filename:
            return {"message": "Bad Request: Invalid file", "message_type": "error"}

        try:
            # Save uploaded file
            filename = os.path.basename(file_field.filename)
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, "wb") as f:
                shutil.copyfileobj(file_field.file, f)

            preset_name = os.path.splitext(filename)[0]
            num_slices = int(form.getvalue('num_slices', 16))
            if not (1 <= num_slices <= 16):
                raise ValueError("Number of slices must be between 1 and 16")

            regions = None
            if 'regions' in form:
                regions = json.loads(form.getvalue('regions'))
                num_slices = None

            result = process_kit(
                input_wav=filepath,
                preset_name=preset_name,
                regions=regions,
                num_slices=num_slices,
                keep_files=False,
                mode=mode
            )

            if mode == "download" and result.get('success'):
                bundle_path = result.get('bundle_path')
                if os.path.exists(bundle_path):
                    with open(bundle_path, "rb") as f:
                        bundle_data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", f"attachment; filename={os.path.basename(bundle_path)}")
                    self.send_header("Content-Length", str(len(bundle_data)))
                    self.end_headers()
                    self.wfile.write(bundle_data)
                    os.remove(bundle_path)
                    return None

            return {
                "message": result.get('message', 'Operation completed successfully'),
                "message_type": "success" if result.get('success') else "error"
            }

        except Exception as e:
            return {"message": f"Error processing kit: {str(e)}", "message_type": "error"}

    @route_handler.post("/refresh")
    def handle_refresh_post(self, form):
        action = form.getvalue('action')
        if action != "refresh_library":
            return {"message": "Bad Request: Invalid action", "message_type": "error"}

        try:
            success, message = refresh_library()
            return {"message": message, "message_type": "success" if success else "error"}
        except Exception as e:
            return {"message": f"Error refreshing library: {str(e)}", "message_type": "error"}

    @route_handler.post("/reverse")
    def handle_reverse_post(self, form):
        action = form.getvalue('action')
        if action != "reverse_file":
            return {"message": "Bad Request: Invalid action", "message_type": "error"}

        wav_file = form.getvalue('wav_file')
        if not wav_file:
            return {"message": "Bad Request: No WAV file selected", "message_type": "error"}

        try:
            success, message = reverse_wav_file(filename=wav_file, directory=BASE_SAMPLES_DIR)
            return {"message": message, "message_type": "success" if success else "error"}
        except Exception as e:
            return {"message": f"Error processing reverse WAV file: {str(e)}", "message_type": "error"}

    def do_POST(self):
        if self.path not in ["/slice", "/refresh", "/reverse"]:
            self.send_error(404)
            return

        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers.get('Content-Type', ''),
                }
            )
        except Exception as e:
            self.send_error(400, str(e))
            return

        handler = self.route_handler.post_routes.get(self.path)
        if not handler:
            self.send_error(404)
            return

        try:
            result = handler(self, form)
            if result is not None:  # None means the handler has already sent the response
                content = self.route_handler.template_manager.render(
                    os.path.basename(self.path) + ".html",
                    **result
                )
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes(content, "utf-8"))
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == "__main__":
    write_pid()
    atexit.register(remove_pid)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)
    
    hostName = "0.0.0.0"
    serverPort = 666
    
    print("Starting webserver")
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print(f"Server started http://{hostName}:{serverPort}")
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")
