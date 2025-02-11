import subprocess

def refresh_library():
    """
    Executes the dbus-send command to refresh the library.
    Returns a tuple (success: bool, message: str).
    """
    try:
        cmd = [
            "dbus-send",
            "--system",
            "--type=method_call",
            "--dest=com.ableton.move",
            "--print-reply",
            "/com/ableton/move/browser",
            "com.ableton.move.Browser.refreshCache"
        ]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        print("Library refreshed successfully.")
        return True, "Library refreshed successfully."
    except subprocess.CalledProcessError as e:
        error_message = e.output.decode().strip() if e.output else "Unknown error."
        print(f"Failed to refresh library: {error_message}")
        return False, f"Failed to refresh library: {error_message}"
    except Exception as e:
        print(f"An error occurred while refreshing library: {e}")
        return False, f"An error occurred while refreshing library: {e}"
