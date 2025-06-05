#!/usr/bin/env python3
"""Flask-based Move webserver using Jinja templates."""
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    jsonify,
    redirect,
    g,
)
import os
import atexit
import signal
import sys
import socket
import numpy as np
import librosa
import time
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
from handlers.reverse_handler_class import ReverseHandler
from handlers.restore_handler_class import RestoreHandler
from handlers.slice_handler_class import SliceHandler
from handlers.set_management_handler_class import SetManagementHandler
from handlers.synth_preset_inspector_handler_class import (
    SynthPresetInspectorHandler,
)
from handlers.drum_rack_inspector_handler_class import DrumRackInspectorHandler
from handlers.file_placer_handler_class import FilePlacerHandler
from handlers.refresh_handler_class import RefreshHandler
from dash import Dash, html, dcc, Input, Output, State
from core.reverse_handler import get_wav_files
import cgi

PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "move-webserver.pid")


class SimpleForm(dict):
    """Mimic ``cgi.FieldStorage`` for our handler classes."""

    def getvalue(self, name, default=None):
        return self.get(name, default)


class FileField(cgi.FieldStorage):
    """Wrapper around Flask ``FileStorage`` objects."""

    def __init__(self, fs):
        self.filename = fs.filename
        self.file = fs.stream


def write_pid():
    """Write the current process ID to ``PID_FILE`` for management."""
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as exc:
        print(f"Error writing PID file: {exc}")


def remove_pid():
    """Remove the PID file on shutdown."""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as exc:
        print(f"Error removing PID file: {exc}")


def handle_exit(signum, frame):
    """Handle termination signals gracefully."""
    print(f"Received signal {signum}, exiting.")
    remove_pid()
    sys.exit(0)


class TLSIgnoringWSGIRequestHandler(WSGIRequestHandler):
    """WSGI request handler that ignores TLS handshake attempts."""
    protocol_version = "HTTP/1.1"

    def handle(self):
        """Check for TLS handshakes before reading the request line."""
        try:
            self.connection.settimeout(0.5)
            peek = self.connection.recv(3, socket.MSG_PEEK)
            self.connection.settimeout(None)
            if peek and len(peek) >= 3 and peek.startswith(b"\x16\x03"):
                print("Ignored TLS handshake attempt (detected in handle)")
                self.close_connection = True
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.connection.close()
                return
        except socket.timeout:
            # No data arrived quickly; proceed with normal handling
            self.connection.settimeout(None)
        except Exception as exc:
            self.connection.settimeout(None)
            err_str = repr(str(exc))
            if "\\x16\\x03" in err_str:
                print(
                    f"Ignored TLS handshake attempt (exception in handle): {err_str[:50]}..."
                )
                self.close_connection = True
                try:
                    self.connection.close()
                except Exception:
                    pass
                return
        super().handle()

    def parse_request(self):
        try:
            self.connection.settimeout(0.5)
            peek = self.connection.recv(5, socket.MSG_PEEK)
            self.connection.settimeout(None)
            if peek and len(peek) >= 3 and peek.startswith(b"\x16\x03"):
                print("Ignored TLS handshake attempt (detected in parse_request)")
                self.close_connection = True
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.connection.close()
                return False
            return super().parse_request()
        except socket.timeout:
            self.connection.settimeout(None)
            return super().parse_request()
        except Exception as exc:
            self.connection.settimeout(None)
            err_str = repr(str(exc))
            if "\\x16\\x03" in err_str:
                print(
                    f"Ignored TLS handshake attempt (exception in parse_request): {err_str[:50]}..."
                )
                self.close_connection = True
                try:
                    self.connection.close()
                except Exception:
                    pass
                return False
            raise


class TLSIgnoringWSGIServer(WSGIServer):
    """WSGIServer that suppresses errors from TLS handshake attempts."""

    def handle_error(self, request, client_address):
        import traceback

        exc_type, exc_value, _ = sys.exc_info()
        is_tls = False
        if exc_value and "\\x16\\x03" in repr(str(exc_value)):
            is_tls = True
        if not is_tls:
            print("-" * 40)
            print("Exception occurred during processing of request from", client_address)
            traceback.print_exc()
            print("-" * 40)


# Threading-enabled WSGI server that ignores TLS handshake attempts
from socketserver import ThreadingMixIn

class ThreadingTLSIgnoringWSGIServer(ThreadingMixIn, TLSIgnoringWSGIServer):
    """Threading-enabled WSGI server that ignores TLS handshake attempts."""
    daemon_threads = True


app = Flask(__name__, template_folder="templates_jinja")
reverse_handler = ReverseHandler()
restore_handler = RestoreHandler()
slice_handler = SliceHandler()
set_management_handler = SetManagementHandler()
synth_handler = SynthPresetInspectorHandler()
file_placer_handler = FilePlacerHandler()
refresh_handler = RefreshHandler()
drum_rack_handler = DrumRackInspectorHandler()
dash_app = Dash(__name__, server=app, routes_pathname_prefix="/dash/")


def dash_layout():
    """Dynamic layout for the Dash interface."""
    return html.Div(
        [
            dcc.Location(id="dash-url"),
            html.H1("Move Dash"),
            html.Nav(
                [
                    dcc.Link("Restore", href="/dash/restore", style={"margin-right": "10px"}),
                    dcc.Link("Reverse", href="/dash/reverse", style={"margin-right": "10px"}),
                    dcc.Link("Slice", href="/dash/slice", style={"margin-right": "10px"}),
                    dcc.Link("MIDI Upload", href="/dash/midi-upload", style={"margin-right": "10px"}),
                    dcc.Link("Synth Macros", href="/dash/synth-macros", style={"margin-right": "10px"}),
                    dcc.Link("Drum Rack", href="/dash/drum-rack-inspector", style={"margin-right": "10px"}),
                    dcc.Link("Refresh", href="/dash/refresh", style={"margin-right": "10px"}),
                ]
            ),
            html.Div(id="dash-page-content"),
        ]
    )


dash_app.layout = dash_layout


def reverse_page_layout():
    """Layout for reversing WAV files."""
    options = [
        {"label": f, "value": f}
        for f in get_wav_files("/data/UserData/UserLibrary/Samples")
    ]
    return html.Div(
        [
            html.H2("Reverse a WAV File"),
            dcc.Dropdown(
                id="reverse-wav-file",
                options=options,
                placeholder="Select a file",
            ),
            html.Button("Reverse", id="reverse-submit"),
            html.Div(id="reverse-message"),
        ]
    )


@dash_app.callback(Output("dash-page-content", "children"), Input("dash-url", "pathname"))
def render_page(pathname):
    if pathname == "/dash/reverse":
        return reverse_page_layout()
    if pathname == "/dash/restore":
        return html.Iframe(src="/restore", style={"width": "100%", "height": "800px", "border": "none"})
    if pathname == "/dash/slice":
        return html.Iframe(src="/slice", style={"width": "100%", "height": "800px", "border": "none"})
    if pathname == "/dash/midi-upload":
        return html.Iframe(src="/midi-upload", style={"width": "100%", "height": "800px", "border": "none"})
    if pathname == "/dash/synth-macros":
        return html.Iframe(src="/synth-macros", style={"width": "100%", "height": "800px", "border": "none"})
    if pathname == "/dash/drum-rack-inspector":
        return html.Iframe(src="/drum-rack-inspector", style={"width": "100%", "height": "800px", "border": "none"})
    if pathname == "/dash/refresh":
        return html.Iframe(src="/refresh", style={"width": "100%", "height": "200px", "border": "none"})
    return html.Div("Select a tool from the navigation.")


@dash_app.callback(
    Output("reverse-message", "children"),
    Input("reverse-submit", "n_clicks"),
    State("reverse-wav-file", "value"),
    prevent_initial_call=True,
)
def perform_reverse(n_clicks, wav_file):
    if not wav_file:
        return "No file selected"
    form = SimpleForm({"action": "reverse_file", "wav_file": wav_file})
    result = reverse_handler.handle_post(form)
    return result.get("message", "")


@app.before_request
def record_start_time():
    """Record the start time of the request."""
    g._start_time = time.perf_counter()


@app.before_request
def enforce_http():
    """Redirect HTTPS requests to HTTP without persistent caching."""
    proto = request.headers.get("X-Forwarded-Proto", "http").lower()
    if proto == "https" or request.is_secure:
        target = request.url.replace("https://", "http://", 1)
        resp = redirect(target, code=307)
        resp.headers["Cache-Control"] = "no-store"
        return resp


@app.after_request
def log_request_time(response):
    """Log how long the request took."""
    start = getattr(g, "_start_time", None)
    if start is not None:
        elapsed = time.perf_counter() - start
        print(f"{request.method} {request.path} took {elapsed:.3f}s")
    return response


def warm_up_modules():
    """Warm-up heavy modules to avoid first-call latency."""
    overall_start = time.perf_counter()
    # Warm-up librosa onset detection
    try:
        start = time.perf_counter()
        y = np.zeros(512, dtype=float)
        librosa.onset.onset_detect(y=y, sr=22050, units="time", delta=0.07)
        print(
            f"Librosa onset_detect warm-up complete in {time.perf_counter() - start:.3f}s."
        )
    except Exception as exc:
        print(f"Error during librosa warm-up: {exc}")

    # Warm-up librosa time_stretch
    try:
        start = time.perf_counter()
        from librosa.effects import time_stretch

        time_stretch(y, rate=1.0)
        print(
            f"Librosa time_stretch warm-up complete in {time.perf_counter() - start:.3f}s."
        )
    except Exception as exc:
        print(f"Error during librosa time_stretch warm-up: {exc}")

    # Warm-up audiotsm WSOLA
    try:
        start = time.perf_counter()
        from audiotsm.io.array import ArrayReader, ArrayWriter
        from audiotsm import wsola

        dummy = np.zeros((1, 512), dtype=float)
        reader = ArrayReader(dummy)
        writer = ArrayWriter(dummy.shape[0])
        tsm = wsola(writer.channels)
        tsm.set_speed(1.0)
        tsm.run(reader, writer)
        print(
            f"Audiotsm WSOLA warm-up complete in {time.perf_counter() - start:.3f}s."
        )
    except Exception as exc:
        print(f"Error during audiotsm WSOLA warm-up: {exc}")

    # Full Librosa onset pipeline
    try:
        start = time.perf_counter()
        y_long = np.zeros(22050, dtype=float)
        librosa.onset.onset_detect(y=y, sr=22050, units="time", delta=0.07)
        y_harm, y_perc = librosa.effects.hpss(y_long)
        o_env = librosa.onset.onset_strength(
            y=y_perc,
            sr=22050,
            hop_length=128,
            n_mels=64,
            fmax=22050 // 2,
            aggregate=np.median,
        )
        if o_env.max() > 0:
            o_env = o_env / o_env.max()
        librosa.util.peak_pick(
            o_env,
            pre_max=2,
            post_max=2,
            pre_avg=2,
            post_avg=2,
            delta=0.07,
            wait=64,
        )
        print(
            f"Librosa onset pipeline warm-up complete in {time.perf_counter() - start:.3f}s."
        )
    except Exception as exc:
        print(f"Error during Librosa warm-up: {exc}")

    print(
        f"Module warm-up finished in {time.perf_counter() - overall_start:.3f}s."
    )


@app.route("/")
def index():
    return redirect("/restore")


@app.route("/reverse", methods=["GET", "POST"])
def reverse():
    message = None
    success = False
    message_type = None
    if request.method == "POST":
        form = SimpleForm(request.form.to_dict())
        result = reverse_handler.handle_post(form)
        message = result.get("message")
        message_type = result.get("message_type")
        success = message_type != "error"
    else:
        message = "Select a WAV file to reverse"
        message_type = "info"
    wav_list = get_wav_files("/data/UserData/UserLibrary/Samples")
    return render_template(
        "reverse.html",
        message=message,
        success=success,
        message_type=message_type,
        wav_files=wav_list,
        active_tab="reverse",
    )


@app.route("/restore", methods=["GET", "POST"])
def restore():
    message = None
    success = False
    message_type = None
    options_html = ""
    if request.method == "POST":
        form_data = request.form.to_dict()
        if "ablbundle" in request.files:
            form_data["ablbundle"] = FileField(request.files["ablbundle"])
        form = SimpleForm(form_data)
        result = restore_handler.handle_post(form)
        message = result.get("message")
        message_type = result.get("message_type")
        success = message_type != "error"
    context = restore_handler.handle_get()
    options_html = context.get("options", "")
    return render_template(
        "restore.html",
        message=message,
        success=success,
        message_type=message_type,
        options_html=options_html,
        active_tab="restore",
    )


@app.route("/slice", methods=["GET", "POST"])
def slice_tool():
    message = None
    success = False
    message_type = None
    if request.method == "POST":
        form_data = request.form.to_dict()
        if "file" in request.files:
            form_data["file"] = FileField(request.files["file"])
        form = SimpleForm(form_data)
        result = slice_handler.handle_post(form)
        if result is not None:
            if result.get("download") and result.get("bundle_path"):
                path = result["bundle_path"]
                resp = send_file(path, as_attachment=True)
                try:
                    os.remove(path)
                except Exception:
                    pass
                return resp
            message = result.get("message")
            message_type = result.get("message_type")
            success = message_type != "error"
    return render_template(
        "slice.html",
        message=message,
        success=success,
        message_type=message_type,
        active_tab="slice",
    )


@app.route("/midi-upload", methods=["GET", "POST"])
def midi_upload():
    message = None
    success = False
    message_type = None
    context = set_management_handler.handle_get()
    pad_options = context.get("pad_options", "")
    pad_color_options = context.get("pad_color_options", "")
    if request.method == "POST":
        form_data = request.form.to_dict()
        if "midi_file" in request.files:
            form_data["midi_file"] = FileField(request.files["midi_file"])
        form = SimpleForm(form_data)
        result = set_management_handler.handle_post(form)
        message = result.get("message")
        message_type = result.get("message_type")
        success = message_type != "error"
        pad_options = result.get("pad_options", pad_options)
    else:
        message = context.get("message")
        message_type = context.get("message_type")
        success = message_type != "error" if message_type else False
    return render_template(
        "midi_upload.html",
        message=message,
        success=success,
        message_type=message_type,
        pad_options=pad_options,
        pad_color_options=pad_color_options,
        active_tab="midi-upload",
    )


@app.route("/synth-macros", methods=["GET", "POST"])
def synth_macros():
    message = None
    success = False
    message_type = None
    options_html = ""
    macros_html = ""
    selected_preset = None
    if request.method == "POST":
        form = SimpleForm(request.form.to_dict())
        result = synth_handler.handle_post(form)
    else:
        result = synth_handler.handle_get()
    message = result.get("message")
    message_type = result.get("message_type")
    success = message_type != "error"
    options_html = result.get("options", "")
    macros_html = result.get("macros_html", "")
    selected_preset = result.get("selected_preset")
    preset_selected = bool(selected_preset)
    return render_template(
        "synth_macros.html",
        message=message,
        success=success,
        message_type=message_type,
        options_html=options_html,
        macros_html=macros_html,
        preset_selected=preset_selected,
        selected_preset=selected_preset,
        active_tab="synth-macros",
    )


@app.route("/chord", methods=["GET"])
def chord():
    return render_template("chord.html", active_tab="chord")


@app.route("/samples/<path:sample_path>", methods=["GET", "OPTIONS"])
def serve_sample(sample_path):
    """Serve sample audio files with CORS headers."""
    from urllib.parse import unquote

    base_dir = "/data/UserData/UserLibrary/Samples/Preset Samples"
    decoded_path = unquote(sample_path)
    full_path = os.path.join(base_dir, decoded_path)

    base_real = os.path.realpath(base_dir)
    file_real = os.path.realpath(full_path)

    if not file_real.startswith(base_real):
        return ("Access denied", 403)

    if not os.path.exists(file_real):
        return ("File not found", 404)

    if request.method == "OPTIONS":
        resp = app.make_response("")
    else:
        resp = send_file(file_real)

    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/drum-rack-inspector", methods=["GET", "POST"])
def drum_rack_inspector():
    message = None
    success = False
    message_type = None
    options_html = ""
    samples_html = ""
    if request.method == "POST":
        form = SimpleForm(request.form.to_dict())
        result = drum_rack_handler.handle_post(form)
    else:
        result = drum_rack_handler.handle_get()
    message = result.get("message")
    message_type = result.get("message_type")
    success = message_type != "error" if message_type else False
    options_html = result.get("options") or result.get("options_html", "")
    samples_html = result.get("samples_html", "")
    return render_template(
        "drum_rack_inspector.html",
        message=message,
        success=success,
        message_type=message_type,
        options_html=options_html,
        samples_html=samples_html,
        active_tab="drum-rack-inspector",
    )


@app.route("/place-files", methods=["POST"])
def place_files_route():
    form_data = request.form.to_dict()
    if "file" in request.files:
        form_data["file"] = FileField(request.files["file"])
    form = SimpleForm(form_data)
    result = file_placer_handler.handle_post(form)
    return jsonify(result)


@app.route("/refresh", methods=["POST"])
def refresh_route():
    form = SimpleForm(request.form.to_dict())
    result = refresh_handler.handle_post(form)
    return jsonify(result)


@app.route("/detect-transients", methods=["POST"])
def detect_transients_route():
    form_data = request.form.to_dict()
    if "file" in request.files:
        form_data["file"] = FileField(request.files["file"])
    form = SimpleForm(form_data)
    resp = slice_handler.handle_detect_transients(form)
    return (
        resp["content"],
        resp.get("status", 200),
        resp.get("headers", [("Content-Type", "application/json")]),
    )


if __name__ == "__main__":
    write_pid()
    atexit.register(remove_pid)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    warm_up_modules()

    host = "0.0.0.0"
    port = 909
    print("Starting webserver", flush=True)
    with make_server(
        host,
        port,
        app,
        server_class=ThreadingTLSIgnoringWSGIServer,
        handler_class=TLSIgnoringWSGIRequestHandler,
    ) as httpd:
        print(f"Server started http://{host}:{port}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
