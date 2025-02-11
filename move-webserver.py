#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import cgi
import atexit
import signal
import sys
from handlers.slice_handler_class import SliceHandler
from handlers.refresh_handler_class import RefreshHandler
from handlers.reverse_handler_class import ReverseHandler

# Define the PID file location
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
            kwargs["options"] = kwargs.get("options", "")
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

class MyServer(BaseHTTPRequestHandler):
    route_handler = RouteHandler()
    
    # Initialize handlers
    slice_handler = SliceHandler()
    refresh_handler = RefreshHandler()
    reverse_handler = ReverseHandler()

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
        return {"options": self.reverse_handler.get_wav_options()}

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

    def send_response_with_headers(self, status, headers, content):
        """Helper method to send response with headers."""
        self.send_response(status)
        for header, value in headers:
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(content)

    @route_handler.post("/slice")
    def handle_slice_post(self, form):
        return self.slice_handler.handle_post(form, self.send_response_with_headers)

    @route_handler.post("/refresh")
    def handle_refresh_post(self, form):
        return self.refresh_handler.handle_post(form)

    @route_handler.post("/reverse")
    def handle_reverse_post(self, form):
        return self.reverse_handler.handle_post(form)

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
