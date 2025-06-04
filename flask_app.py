#!/usr/bin/env python3
"""Simple Flask app using Jinja templates.

This example shows how parts of ``move-webserver.py`` can be served
via Flask.  Only the reverse, restore, and slice tools are
implemented to demonstrate the approach.
"""
from flask import Flask, render_template, request, send_file, jsonify, redirect
import os
from handlers.reverse_handler_class import ReverseHandler
from handlers.restore_handler_class import RestoreHandler
from handlers.slice_handler_class import SliceHandler
from handlers.set_management_handler_class import SetManagementHandler
from handlers.synth_preset_inspector_handler_class import SynthPresetInspectorHandler
from handlers.file_placer_handler_class import FilePlacerHandler
from handlers.refresh_handler_class import RefreshHandler
from dash import Dash, html
from core.reverse_handler import get_wav_files
import cgi


class SimpleForm(dict):
    """Mimic ``cgi.FieldStorage`` for our handler classes."""

    def getvalue(self, name, default=None):
        return self.get(name, default)


class FileField(cgi.FieldStorage):
    """Wrapper around Flask ``FileStorage`` objects."""

    def __init__(self, fs):
        self.filename = fs.filename
        self.file = fs.stream

app = Flask(__name__, template_folder="templates_jinja")
reverse_handler = ReverseHandler()
restore_handler = RestoreHandler()
slice_handler = SliceHandler()
set_management_handler = SetManagementHandler()
synth_handler = SynthPresetInspectorHandler()
file_placer_handler = FilePlacerHandler()
refresh_handler = RefreshHandler()
dash_app = Dash(__name__, server=app, routes_pathname_prefix="/dash/")
dash_app.layout = html.Div([html.H1("Move Dash"), html.P("Placeholder")])


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
        if 'ablbundle' in request.files:
            form_data['ablbundle'] = FileField(request.files['ablbundle'])
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
        if 'file' in request.files:
            form_data['file'] = FileField(request.files['file'])
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


@app.route("/set-management", methods=["GET", "POST"])
def set_management():
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
        "set_management.html",
        message=message,
        success=success,
        message_type=message_type,
        pad_options=pad_options,
        pad_color_options=pad_color_options,
        active_tab="set-management",
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


@app.route("/place-files", methods=["POST"])
def place_files_route():
    form_data = request.form.to_dict()
    if 'file' in request.files:
        form_data['file'] = FileField(request.files['file'])
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
    if 'file' in request.files:
        form_data['file'] = FileField(request.files['file'])
    form = SimpleForm(form_data)
    resp = slice_handler.handle_detect_transients(form)
    return resp["content"], resp.get("status", 200), resp.get(
        "headers", [("Content-Type", "application/json")]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
