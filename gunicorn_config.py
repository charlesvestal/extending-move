import os
import importlib.util
from pathlib import Path

# Dynamically load the main server module which uses a hyphen in the filename
spec = importlib.util.spec_from_file_location(
    "move_webserver", Path(__file__).with_name("move-webserver.py")
)
move_webserver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(move_webserver)

write_pid = move_webserver.write_pid
remove_pid = move_webserver.remove_pid
warm_up_modules = move_webserver.warm_up_modules

# Use custom worker that ignores TLS handshake attempts
worker_class = "tls_worker.TLSDroppingWorker"

# Log to a single file so logs are easy to find
accesslog = "move-webserver.log"
errorlog = "move-webserver.log"

# Preload the app so workers share memory and warm-up runs once
preload_app = True

# Bind to the same port used by the legacy server
bind = "0.0.0.0:909"

# Number of worker processes; default to 2 if not specified
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))

# Write PID and warm-up when the server starts

def on_starting(server):
    write_pid()
    warm_up_modules()

# Remove PID file on shutdown

def on_exit(server):
    remove_pid()
