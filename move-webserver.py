#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import atexit
import signal
import sys
import cgi
import numpy as np
import librosa
from handlers.slice_handler_class import SliceHandler
from handlers.refresh_handler_class import RefreshHandler
from handlers.reverse_handler_class import ReverseHandler
from handlers.drum_rack_inspector_handler_class import DrumRackInspectorHandler
from handlers.restore_handler_class import RestoreHandler
from handlers.file_placer_handler_class import FilePlacerHandler
from handlers.synth_preset_inspector_handler_class import SynthPresetInspectorHandler
from handlers.set_management_handler_class import SetManagementHandler
from core.config import SAMPLES_PRESET_DIR

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

        # Ensure all templates correctly replace `{{ options }}`
        if "options" in kwargs:
            template = template.replace("{{ options }}", kwargs["options"])

        # Ensure `{{ samples_html }}` is replaced if used
        if "samples_html" in kwargs:
            template = template.replace("{{ samples_html }}", kwargs["samples_html"])

        # Ensure `{{ macros_html }}` is replaced if used
        if "macros_html" in kwargs:
            template = template.replace("{{ macros_html }}", kwargs["macros_html"])

        # Add pad_options and pad_color_options replacements
        if "pad_options" in kwargs:
            template = template.replace("{{ pad_options }}", kwargs["pad_options"])
        if "pad_color_options" in kwargs:
            template = template.replace("{{ pad_color_options }}", kwargs["pad_color_options"])

        # Ensure message replacement works properly in ALL templates
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
    - TLS handshake attempt filtering
    """
    
    def parse_request(self):
        """
        Override parse_request to catch and ignore TLS handshake attempts.
        This prevents errors when clients try to connect using HTTPS.
        """
        try:
            # Check if this is a TLS handshake attempt before parsing
            if hasattr(self, 'rfile'):
                # Peek at the first few bytes without consuming them
                peek_data = self.rfile.peek(5)
                if peek_data and len(peek_data) >= 3 and peek_data.startswith(b'\x16\x03'):
                    # This is a TLS handshake attempt, silently ignore it
                    print("Ignored TLS handshake attempt (detected in parse_request)")
                    # Consume the data to prevent further errors
                    self.rfile.read()
                    return False
            
            # Call the original method
            return super().parse_request()
        except Exception as e:
            # Check if this looks like a TLS handshake attempt
            err_str = repr(str(e))
            if "\\x16\\x03" in err_str:
                # This is likely a TLS handshake attempt, silently ignore it
                print(f"Ignored TLS handshake attempt (exception in parse_request): {err_str[:50]}...")
                return False
            # Re-raise other exceptions
            raise
    route_handler = RouteHandler()
    
    # Initialize feature handlers
    slice_handler = SliceHandler()
    refresh_handler = RefreshHandler()
    reverse_handler = ReverseHandler()
    drum_rack_inspector_handler = DrumRackInspectorHandler()
    restore_handler = RestoreHandler()
    file_placer_handler = FilePlacerHandler()
    synth_preset_inspector_handler = SynthPresetInspectorHandler()
    set_management_handler = SetManagementHandler()
    @route_handler.get("/set-management", "set_management.html")
    def handle_set_management_get(self):
        """Handle GET request for Set Management page."""
        print("DEBUG: /set-management GET called")
        import sys; sys.stdout.flush()
        return self.set_management_handler.handle_get()

    @route_handler.post("/set-management")
    def handle_set_management_post(self, form):
        """Handle POST request to create a new set."""
        return self.set_management_handler.handle_post(form)

    @route_handler.get("/chord", "chord.html")
    def handle_chord_get(self):
        """Simple GET handler for chord page; all processing is client-side."""
        return {}

    @route_handler.get("/restore", "restore.html")
    def handle_restore_get(self):
        """Handles GET request for the restore page."""
        context = self.restore_handler.handle_get()
        print(f"DEBUG: Rendering restore.html with options -> {context['options']}")  # ✅ Debug print
        return context

    @route_handler.get("/refresh_library", "refresh.html")
    def handle_refresh_library_get(self):
        """Handle GET request for refreshing the library without additional inputs."""
        from core.refresh_handler import refresh_library  # Import locally
        try:
            success, message = refresh_library()
            if success:
                return {"message": f"<p style='color: green;'>{message}</p>"}
            else:
                return {"message": f"<p style='color: red;'>{message}</p>"}
        except Exception as e:
            return {"message": f"<p style='color: red;'>Error refreshing library: {str(e)}</p>"}

    @route_handler.get("/", "index.html")
    def handle_index(self):
        """Handle GET request for index page."""
        return {}

    @route_handler.get("/chord", "chord.html")
    def handle_chord_get(self):
        """Serve chord.html with no server-side chord processing."""
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

    @route_handler.get("/synth-preset-inspector", "synth_preset_inspector.html")
    def handle_synth_preset_inspector_get(self):
        """Handle GET request for synth preset inspector page."""
        return self.synth_preset_inspector_handler.handle_get()

    @route_handler.post("/synth-preset-inspector")
    def handle_synth_preset_inspector_post(self, form):
        """Handle POST request for synth preset inspector page."""
        return self.synth_preset_inspector_handler.handle_post(form)

    @route_handler.post("/detect-transients")
    def handle_detect_transients_post(self, form):
        resp = self.slice_handler.handle_detect_transients(form)
        return resp["status"], resp["headers"], resp["content"]

    def handle_static_file(self, path):
        """Handle requests for static files."""
        try:
            # Remove the leading '/static/' from the path
            relative_path = path[8:]  # len('/static/') = 8
            
            # Construct the full path to the static file
            full_path = os.path.join('static', relative_path)
            
            # Security check: ensure the requested path is within the static directory
            real_path = os.path.realpath(full_path)
            if not real_path.startswith(os.path.realpath('static')):
                self.send_error(403, "Access denied")
                return
            
            if not os.path.exists(real_path):
                self.send_error(404, "File not found")
                return
                
            # Read and serve the file
            with open(real_path, 'rb') as f:
                content = f.read()
                
            # Determine content type based on file extension
            content_type = 'text/plain'
            if real_path.endswith('.css'):
                content_type = 'text/css'
            elif real_path.endswith('.js'):
                content_type = 'text/javascript'
                
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, str(e))

    def handle_sample_request(self, path):
        """Handle requests for sample files."""
        try:
            # Remove the leading '/samples/' from the path
            relative_path = path[9:]  # len('/samples/') = 9
            
            # URL decode the path
            from urllib.parse import unquote
            relative_path = unquote(relative_path)
            
            # Construct the full path to the samples directory
            base_samples_dir = SAMPLES_PRESET_DIR
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
        elif self.path.startswith('/static/'):
            self.handle_static_file(self.path)
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

    @route_handler.post("/place-files")
    def handle_place_files(self, form):
        return self.file_placer_handler.handle_post(form)


    @route_handler.post("/restore")
    def handle_restore_post(self, form):
        """Handles POST request for restoring an .ablbundle file."""
        return self.restore_handler.handle_post(form)

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
        if self.path not in ["/slice", "/refresh", "/reverse", "/drum-rack-inspector", "/restore", "/chord", "/place-files", "/synth-preset-inspector", "/detect-transients", "/set-management"]:
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
                # Special handling for handlers that return (status, headers, content) tuple
                if isinstance(result, tuple) and len(result) == 3:
                    status, headers, content = result
                    self.send_response(status)
                    for header, value in headers:
                        self.send_header(header, value)
                    self.end_headers()
                    if isinstance(content, str):
                        content = content.encode("utf-8")
                    self.wfile.write(content)
                    return
                if self.path == "/place-files":
                    import json
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(bytes(json.dumps(result), "utf-8"))
                    return
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

class TLSIgnoringHTTPServer(HTTPServer):
    """
    Custom HTTP server that ignores TLS handshake attempts.
    This prevents errors when clients try to connect using HTTPS.
    """
    
    def handle_error(self, request, client_address):
        """
        Override handle_error to ignore TLS handshake attempts.
        """
        import traceback
        import sys
        
        # Get the exception info
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Check if this is a TLS handshake attempt
        is_tls_handshake = False
        
        # Check exception message for TLS handshake signature
        if exc_value and "\\x16\\x03" in repr(str(exc_value)):
            is_tls_handshake = True
        
        # If it's not a TLS handshake attempt, log the error as usual
        if not is_tls_handshake:
            print('-'*40)
            print('Exception occurred during processing of request from', client_address)
            traceback.print_exc()
            print('-'*40)

if __name__ == "__main__":
    write_pid()
    atexit.register(remove_pid)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)
    
    hostName = "0.0.0.0"
    serverPort = 909
    
    print("Starting webserver")
    webServer = TLSIgnoringHTTPServer((hostName, serverPort), MyServer)
    print(f"Server started http://{hostName}:{serverPort}")
    
    # Warm-up librosa onset detection to avoid first-call latency
    try:
        y = np.zeros(512, dtype=float)
        librosa.onset.onset_detect(y=y, sr=22050, units='time', delta=0.07)
        print("Librosa onset_detect warm-up complete.")
    except Exception as e:
        print(f"Error during librosa warm-up: {e}")

    # Warm-up librosa time_stretch for phase vocoder
    try:
        from librosa.effects import time_stretch
        time_stretch(y, rate=1.0)
        print("Librosa time_stretch warm-up complete.")
    except Exception as e:
        print(f"Error during librosa time_stretch warm-up: {e}")

    # Warm-up audiotsm WSOLA to compile JIT and FFT routines
    try:
        from audiotsm.io.array import ArrayReader, ArrayWriter
        from audiotsm import wsola
        # Dummy mono audio data: shape (channels, frames)
        dummy = np.zeros((1, 512), dtype=float)
        reader = ArrayReader(dummy)
        writer = ArrayWriter(dummy.shape[0])
        tsm = wsola(writer.channels)
        tsm.set_speed(1.0)
        tsm.run(reader, writer)
        print("Audiotsm WSOLA warm-up complete.")
    except Exception as e:
        print(f"Error during audiotsm WSOLA warm-up: {e}")
    
    # Warm-up the full Librosa onset pipeline (basic + advanced)
    try:
        # 1) Basic onset_detect warm-up
        y = np.zeros(512, dtype=float)
        librosa.onset.onset_detect(y=y, sr=22050, units='time', delta=0.07)

        # 2) HPSS + onset_strength + peak_pick warm-up
        y_long = np.zeros(22050, dtype=float)  # 1 second of silence
        y_harm, y_perc = librosa.effects.hpss(y_long)
        o_env = librosa.onset.onset_strength(
            y=y_perc,
            sr=22050,
            hop_length=128,
            n_mels=64,
            fmax=22050//2,
            aggregate=np.median
        )
        if o_env.max() > 0:
            o_env = o_env / o_env.max()
        # Use the same peak-picker parameters you ship to the user
        librosa.util.peak_pick(
            o_env,
            pre_max=2, post_max=2,
            pre_avg=2, post_avg=2,
            delta=0.07, wait=128//2
        )

        print("Librosa onset pipeline warm-up complete.")
    except Exception as e:
        print(f"Error during Librosa warm-up: {e}")


    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")

    @route_handler.post("/detect-transients")
    def handle_detect_transients(self, form):
        return self.slice_handler.handle_detect_transients(form)
