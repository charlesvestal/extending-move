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
import logging
import numpy as np
import librosa
import time
from wsgiref.simple_server import make_server, WSGIServer
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
from dash import Dash, html
from core.file_browser import generate_dir_html
import cgi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("server.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

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
        logger.error("Error writing PID file: %s", exc)


def remove_pid():
    """Remove the PID file on shutdown."""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as exc:
        logger.error("Error removing PID file: %s", exc)


def handle_exit(signum, frame):
    """Handle termination signals gracefully."""
    logger.info("Received signal %s, exiting.", signum)
    remove_pid()
    sys.exit(0)


from socketserver import ThreadingMixIn


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """Simple threading-capable WSGI server."""

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
dash_app.layout = html.Div([html.H1("Move Dash"), html.P("Placeholder")])


@app.before_request
def record_start_time():
    """Record the start time of the request."""
    g._start_time = time.perf_counter()


@app.after_request
def log_request_time(response):
    """Log how long the request took."""
    start = getattr(g, "_start_time", None)
    if start is not None:
        elapsed = time.perf_counter() - start
        logger.info("%s %s took %.3fs", request.method, request.path, elapsed)
    return response


def warm_up_modules():
    """Warm-up heavy modules to avoid first-call latency."""
    overall_start = time.perf_counter()
    # Warm-up librosa onset detection
    try:
        start = time.perf_counter()
        y = np.zeros(512, dtype=float)
        librosa.onset.onset_detect(y=y, sr=22050, units="time", delta=0.07)
        logger.info(
            "Librosa onset_detect warm-up complete in %.3fs",
            time.perf_counter() - start,
        )
    except Exception as exc:
        logger.error("Error during librosa warm-up: %s", exc)

    # Warm-up librosa time_stretch
    try:
        start = time.perf_counter()
        from librosa.effects import time_stretch

        time_stretch(y, rate=1.0)
        logger.info(
            "Librosa time_stretch warm-up complete in %.3fs",
            time.perf_counter() - start,
        )
    except Exception as exc:
        logger.error("Error during librosa time_stretch warm-up: %s", exc)

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
        logger.info(
            "Audiotsm WSOLA warm-up complete in %.3fs",
            time.perf_counter() - start,
        )
    except Exception as exc:
        logger.error("Error during audiotsm WSOLA warm-up: %s", exc)

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
        logger.info(
            "Librosa onset pipeline warm-up complete in %.3fs",
            time.perf_counter() - start,
        )
    except Exception as exc:
        logger.error("Error during Librosa warm-up: %s", exc)

    logger.info(
        "Module warm-up finished in %.3fs", time.perf_counter() - overall_start
    )


@app.route("/")
def index():
    return redirect("/restore")


@app.route("/browse-dir")
def browse_dir():
    root = request.args.get("root", "")
    path = request.args.get("path", "")
    action_url = request.args.get("action_url", "")
    field_name = request.args.get("field_name", "")
    action_value = request.args.get("action_value", "")
    filter_key = request.args.get("filter")
    html = generate_dir_html(root, path, action_url, field_name, action_value, filter_key)
    return html


@app.route("/reverse", methods=["GET", "POST"])
def reverse():
    message = None
    success = False
    message_type = None
    if request.method == "POST":
        form = SimpleForm(request.form.to_dict())
        result = reverse_handler.handle_post(form)
    else:
        result = reverse_handler.handle_get()
    message = result.get("message")
    message_type = result.get("message_type")
    success = message_type != "error" if message_type else False
    browser_html = result.get("file_browser_html")
    selected_file = result.get("selected_file")
    browser_root = result.get("browser_root")
    browser_filter = result.get("browser_filter")
    return render_template(
        "reverse.html",
        message=message,
        success=success,
        message_type=message_type,
        file_browser_html=browser_html,
        selected_file=selected_file,
        browser_root=browser_root,
        browser_filter=browser_filter,
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
    if request.method == "POST":
        form = SimpleForm(request.form.to_dict())
        result = synth_handler.handle_post(form)
    else:
        result = synth_handler.handle_get()

    message = result.get("message")
    message_type = result.get("message_type")
    success = message_type != "error" if message_type else False
    browser_html = result.get("file_browser_html")
    browser_root = result.get("browser_root")
    browser_filter = result.get("browser_filter")
    macros_html = result.get("macros_html", "")
    selected_preset = result.get("selected_preset")
    preset_selected = bool(selected_preset)
    return render_template(
        "synth_macros.html",
        message=message,
        success=success,
        message_type=message_type,
        file_browser_html=browser_html,
        browser_root=browser_root,
        browser_filter=browser_filter,
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
    if request.method == "POST":
        form = SimpleForm(request.form.to_dict())
        result = drum_rack_handler.handle_post(form)
    else:
        result = drum_rack_handler.handle_get()

    message = result.get("message")
    message_type = result.get("message_type")
    success = message_type != "error" if message_type else False
    browser_html = result.get("file_browser_html")
    browser_root = result.get("browser_root")
    browser_filter = result.get("browser_filter")
    samples_html = result.get("samples_html", "")
    selected_preset = result.get("selected_preset")
    return render_template(
        "drum_rack_inspector.html",
        message=message,
        success=success,
        message_type=message_type,
        file_browser_html=browser_html,
        browser_root=browser_root,
        browser_filter=browser_filter,
        samples_html=samples_html,
        selected_preset=selected_preset,
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
    logger.info("Starting webserver")
    with make_server(
        host,
        port,
        app,
        server_class=ThreadingWSGIServer,
    ) as httpd:
        logger.info("Server started http://%s:%s", host, port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
