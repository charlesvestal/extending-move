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
        
        print(f"Executing D-Bus command: {' '.join(cmd)}")
        
        # Execute command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        print(f"Command exit code: {result.returncode}")
        print(f"Command stdout: {result.stdout}")
        print(f"Command stderr: {result.stderr}")
        
        if result.returncode == 0:
            print("Library refreshed successfully.")
            return True, "Library refreshed successfully. Move's library cache has been updated."
        else:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            if not error_msg:
                error_msg = f"Command failed with exit code {result.returncode}"
            print(f"Failed to refresh library: {error_msg}")
            return False, f"Failed to refresh library: {error_msg}"
            
    except subprocess.TimeoutExpired:
        error_msg = "D-Bus command timed out after 10 seconds"
        print(error_msg)
        return False, error_msg
    except subprocess.CalledProcessError as e:
        # Handle D-Bus command failure
        error_message = e.output.decode().strip() if e.output else f"Command failed with exit code {e.returncode}"
        print(f"Failed to refresh library: {error_message}")
        return False, f"Failed to refresh library: {error_message}"
    except Exception as e:
        # Handle any other unexpected errors
        error_msg = f"An error occurred while refreshing library: {e}"
        print(error_msg)
        return False, error_msg
