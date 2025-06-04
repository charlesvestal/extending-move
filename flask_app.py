#!/usr/bin/env python3
"""Simple Flask app using Jinja templates.

This is a minimal example showing how the Move server logic can
be wrapped in a Flask application. Only a subset of the features
from ``move-webserver.py`` are implemented as a demonstration.
"""
from flask import Flask, render_template, request
from handlers.reverse_handler_class import ReverseHandler
from handlers.restore_handler_class import RestoreHandler
from dash import Dash, html
from core.reverse_handler import get_wav_files
import cgi

app = Flask(__name__, template_folder="templates_jinja")
reverse_handler = ReverseHandler()
restore_handler = RestoreHandler()
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
        class SimpleForm(dict):
            def getvalue(self, name):
                return self.get(name)

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
        class SimpleForm(dict):
            def getvalue(self, name):
                return self.get(name)

        class FileField(cgi.FieldStorage):
            def __init__(self, fs):
                self.filename = fs.filename
                self.file = fs.stream

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
