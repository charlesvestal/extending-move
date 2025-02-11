import subprocess

def refresh_library():
    """
    Executes the dbus-send command to refresh the Move library cache.
    This is required after adding or modifying files in the library to make them visible in Move.
    
    The command uses the system D-Bus to communicate with Move's browser service:
    - Uses system bus (--system)
    - Calls method refreshCache on com.ableton.move.Browser interface
    - Destination is com.ableton.move
    - Object path is /com/ableton/move/browser
    
    Returns:
        tuple: (success: bool, message: str)
        - success: True if refresh succeeded, False otherwise
        - message: Success or error message describing the result
    """
    try:
        # Construct D-Bus command to refresh Move's library cache
        cmd = [
            "dbus-send",          # D-Bus command line tool
            "--system",           # Use system bus (not session bus)
            "--type=method_call", # This is a method call (not a signal)
            "--dest=com.ableton.move",  # Target service
            "--print-reply",      # Print the reply for debugging
            "/com/ableton/move/browser",  # Object path
            "com.ableton.move.Browser.refreshCache"  # Method to call
        ]
        # Execute command and capture output
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        print("Library refreshed successfully.")
        return True, "Library refreshed successfully."
    except subprocess.CalledProcessError as e:
        # Handle D-Bus command failure
        error_message = e.output.decode().strip() if e.output else "Unknown error."
        print(f"Failed to refresh library: {error_message}")
        return False, f"Failed to refresh library: {error_message}"
    except Exception as e:
        # Handle any other unexpected errors
        print(f"An error occurred while refreshing library: {e}")
        return False, f"An error occurred while refreshing library: {e}"
