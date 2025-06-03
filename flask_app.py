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

app = Flask(__name__, template_folder="templates_jinja")
reverse_handler = ReverseHandler()
restore_handler = RestoreHandler()
dash_app = Dash(__name__, server=app, routes_pathname_prefix="/dash/")
dash_app.layout = html.Div([html.H1("Move Dash"), html.P("Placeholder")])


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reverse", methods=["GET", "POST"])
def reverse():
    message = None
    success = False
    if request.method == "POST":
        form = request.form.to_dict(flat=False)
        # Flask wraps file fields in request.files
        class SimpleForm(dict):
            def getvalue(self, name):
                if name in self:
                    return self[name]
                if name in request.files:
                    return request.files[name]
                return None
        form.update({k: v[0] if isinstance(v, list) else v for k, v in form.items()})
        form = SimpleForm(form)
        result = reverse_handler.handle_post(form)
        message = result.get("message")
        success = result.get("message_type") != "error"
    wav_files = reverse_handler.get_wav_options()
    wav_list = [line.split('>')[1].split('<')[0] for line in wav_files.splitlines() if line.strip()]
    return render_template("reverse.html", message=message, success=success, wav_files=wav_list)

@app.route("/restore", methods=["GET", "POST"])
def restore():
    message = None
    success = False
    pad_options = []
    if request.method == "POST":
        class SimpleForm(dict):
            def getvalue(self, name):
                if name in self:
                    return self[name]
                if name in request.files:
                    return request.files[name]
                return None
        form_data = request.form.to_dict(flat=False)
        form_data.update({k: v.filename if hasattr(v, 'filename') else v for k, v in request.files.items()})
        simple = SimpleForm({k: v[0] if isinstance(v, list) else v for k, v in form_data.items()})
        result = restore_handler.handle_post(simple)
        message = result.get("message")
        success = result.get("message_type") != "error"
    context = restore_handler.handle_get()
    pad_options = [opt.split('>')[1].split('<')[0] for opt in context.get('options','').splitlines() if opt.strip()]
    return render_template("restore.html", message=message, success=success, pad_options=pad_options)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
