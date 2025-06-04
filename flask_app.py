#!/usr/bin/env python3
"""Simple Flask app using Jinja templates.

This example shows how parts of ``move-webserver.py`` can be served
via Flask.  Only the reverse, restore, and slice tools are
implemented to demonstrate the approach.
"""
from flask import Flask, render_template, request, send_file
import os
from handlers.reverse_handler_class import ReverseHandler
from handlers.restore_handler_class import RestoreHandler
from handlers.slice_handler_class import SliceHandler
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
dash_app = Dash(__name__, server=app, routes_pathname_prefix="/dash/")
dash_app.layout = html.Div([html.H1("Move Dash"), html.P("Placeholder")])


@app.route("/")
def index():
    return render_template("index.html", active_tab="home")

@app.route("/reverse", methods=["GET", "POST"])
def reverse():
    message = None
    success = False
    if request.method == "POST":
        form = SimpleForm(request.form.to_dict())
        result = reverse_handler.handle_post(form)
        message = result.get("message")
        success = result.get("message_type") != "error"
    wav_list = get_wav_files("/data/UserData/UserLibrary/Samples")
    return render_template(
        "reverse.html",
        message=message,
        success=success,
        wav_files=wav_list,
        active_tab="reverse",
    )

@app.route("/restore", methods=["GET", "POST"])
def restore():
    message = None
    success = False
    options_html = ""
    if request.method == "POST":
        form_data = request.form.to_dict()
        if 'ablbundle' in request.files:
            form_data['ablbundle'] = FileField(request.files['ablbundle'])
        form = SimpleForm(form_data)
        result = restore_handler.handle_post(form)
        message = result.get("message")
        success = result.get("message_type") != "error"
    context = restore_handler.handle_get()
    options_html = context.get("options", "")
    return render_template(
        "restore.html",
        message=message,
        success=success,
        options_html=options_html,
        active_tab="restore",
    )

@app.route("/slice", methods=["GET", "POST"])
def slice_tool():
    message = None
    success = False
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
            success = result.get("message_type") != "error"
    return render_template(
        "slice.html",
        message=message,
        success=success,
        active_tab="slice",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
