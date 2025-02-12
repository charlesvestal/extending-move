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
from handlers.drum_rack_inspector_handler_class import DrumRackInspectorHandler

# Define the PID file location
PID_FILE = os.path.expanduser('~/extending-move/move-webserver.pid')

class TemplateManager:
    """
    Manages HTML templates with caching and rendering capabilities.
    
    This class handles:
    - Loading templates from the templates directory
    - Caching templates to avoid repeated file reads
    - Rendering templates with variable substitution
    - Special case handling for specific templates
    """
    def __init__(self, template_dir="templates"):
        """Initialize with template directory path and empty cache."""
        self.template_dir = template_dir
        self.templates = {}

    def get_template(self, template_name):
        """
        Get a template by name, loading from disk if not cached.
        
        Args:
            template_name: Name of the template file
        
        Returns:
            str: The template content
        """
        if template_name not in self.templates:
            path = os.path.join(self.template_dir, template_name)
            with open(path, "r") as f:
                self.templates[template_name] = f.read()
        return self.templates[template_name]

    def render(self, template_name, **kwargs):
        """
        Render a template with the provided variables.
        
        Args:
            template_name: Name of the template file
            **kwargs: Variables to substitute in the template
        
        Returns:
            str: The rendered template with all substitutions applied
        """
        template = self.get_template(template_name)
        # Handle special cases
        # Handle template variables
        if template_name in ["reverse.html", "drum_rack_inspector.html"]:
            kwargs["options"] = kwargs.get("options", "")
            template = template.replace("{{ options }}", kwargs["options"])
            
            if template_name == "drum_rack_inspector.html":
                kwargs["samples_html"] = kwargs.get("samples_html", "")
                template = template.replace("{{ samples_html }}", kwargs["samples_html"])
        
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
    """
    Handles route registration and management using decorators.
    
    This class provides:
    - Decorator-based route registration for GET and POST
    - Template management integration
    - Content type handling
    """
    def __init__(self):
        """Initialize with empty route collections and template manager."""
        self.get_routes = {}
        self.post_routes = {}
        self.template_manager = TemplateManager()

    def get(self, path, template_name=None, content_type="text/html"):
        """
        Decorator for registering GET route handlers.
        
        Args:
            path: URL path to handle
            template_name: Optional template to render
            content_type: Response content type
        """
        def decorator(handler):
            self.get_routes[path] = {
                "handler": handler,
                "template": template_name,
                "content_type": content_type
            }
            return handler
        return decorator

    def post(self, path):
        """
        Decorator for registering POST route handlers.
        
        Args:
            path: URL path to handle
        """
        def decorator(handler):
            self.post_routes[path] = handler
            return handler
        return decorator

def write_pid():
    """
    Write the current process PID to the PID_FILE.
    Used for process management and cleanup.
    """
    pid = os.getpid()
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(pid))
        print(f"PID {pid} written to {PID_FILE}")
    except Exception as e:
        print(f"Error writing PID file: {e}")

def remove_pid():
    """
    Remove the PID file.
    Called on server shutdown for cleanup.
    """
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print(f"PID file {PID_FILE} removed.")
    except Exception as e:
        print(f"Error removing PID file: {e}")

def handle_exit(signum, frame):
    """
    Handle termination signals gracefully.
    Ensures clean shutdown on SIGTERM/SIGINT.
    """
    print(f"Received signal {signum}, exiting gracefully.")
    sys.exit(0)

class MyServer(BaseHTTPRequestHandler):
    """
    HTTP request handler for the Move webserver.
    
    Handles:
    - GET/POST requests
    - Route matching
    - Template rendering
    - Response formatting
    - Error handling
    """
    route_handler = RouteHandler()
    
    # Initialize feature handlers
    slice_handler = SliceHandler()
    refresh_handler = RefreshHandler()
    reverse_handler = ReverseHandler()
    drum_rack_inspector_handler = DrumRackInspectorHandler()

    @route_handler.get("/", "index.html")
    def handle_index(self):
        """Handle GET request for index page."""
        return {}

    @route_handler.get("/slice", "slice.html")
    def handle_slice_get(self):
        """Handle GET request for slice page."""
        return {}

    @route_handler.get("/refresh", "refresh.html")
    def handle_refresh_get(self):
        """Handle GET request for refresh page."""
        return {}

    @route_handler.get("/reverse", "reverse.html")
    def handle_reverse_get(self):
        """Handle GET request for reverse page."""
        return {"options": self.reverse_handler.get_wav_options()}

    @route_handler.get("/drum-rack-inspector", "drum_rack_inspector.html")
    def handle_drum_rack_inspector_get(self):
        """Handle GET request for drum rack inspector page."""
        return self.drum_rack_inspector_handler.handle_get()

    @route_handler.get("/style.css", "style.css", "text/css")
    def handle_css(self):
        """Handle GET request for stylesheet."""
        return {}

    def handle_sample_request(self, path):
        """Handle requests for sample files."""
        try:
            # Remove the leading '/samples/' from the path
            relative_path = path[9:]  # len('/samples/') = 9
            
            # URL decode the path
            from urllib.parse import unquote
            relative_path = unquote(relative_path)
            
            # Construct the full path to the samples directory
            base_samples_dir = '/data/UserData/UserLibrary/Samples/Preset Samples'
            full_path = os.path.join(base_samples_dir, relative_path)
            
            # Security check: ensure the requested path is within the samples directory
            real_path = os.path.realpath(full_path)
            
            # Debug logging
            print(f"Debug - Sample request:")
            print(f"Original path: {path}")
            print(f"Relative path: {relative_path}")
            print(f"Full path: {full_path}")
            print(f"Real path: {real_path}")
            print(f"Base dir: {base_samples_dir}")
            print(f"File exists: {os.path.exists(real_path)}")
            if not real_path.startswith(os.path.realpath(base_samples_dir)):
                self.send_error(403, "Access denied")
                return
            
            if not os.path.exists(real_path):
                self.send_error(404, "File not found")
                return
                
            # Read and serve the file
            with open(real_path, 'rb') as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-Type', 'audio/wav')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """
        Handle all GET requests.
        Matches routes and renders appropriate templates.
        """
        if self.path.startswith('/samples/'):
            self.handle_sample_request(self.path)
            return
            
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
        """
        Helper method to send response with custom headers.
        Used primarily for file downloads.
        """
        self.send_response(status)
        for header, value in headers:
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(content)

    @route_handler.post("/slice")
    def handle_slice_post(self, form):
        """Handle POST request for slice feature."""
        return self.slice_handler.handle_post(form, self.send_response_with_headers)

    @route_handler.post("/refresh")
    def handle_refresh_post(self, form):
        """Handle POST request for refresh feature."""
        return self.refresh_handler.handle_post(form)

    @route_handler.post("/reverse")
    def handle_reverse_post(self, form):
        """Handle POST request for reverse feature."""
        return self.reverse_handler.handle_post(form)

    @route_handler.post("/drum-rack-inspector")
    def handle_drum_rack_inspector_post(self, form):
        """Handle POST request for drum rack inspector feature."""
        return self.drum_rack_inspector_handler.handle_post(form)

    def do_POST(self):
        """
        Handle all POST requests.
        Processes form data and delegates to appropriate handler.
        """
        if self.path not in ["/slice", "/refresh", "/reverse", "/drum-rack-inspector"]:
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
                # Convert hyphenated path to underscore for template name
                template_name = os.path.basename(self.path).replace("-", "_") + ".html"
                content = self.route_handler.template_manager.render(
                    template_name,
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
