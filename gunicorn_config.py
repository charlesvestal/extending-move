import os
from move-webserver import write_pid, remove_pid, warm_up_modules

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
