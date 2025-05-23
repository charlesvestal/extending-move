#!/usr/bin/env python3
"""
Simple startup script for the FastAPI version of Move Extended
"""
import subprocess
import sys
import os

def check_requirements():
    """Check if required packages are installed."""
    try:
        import fastapi
        import uvicorn
        print("✓ FastAPI dependencies found")
        return True
    except ImportError:
        print("✗ FastAPI dependencies not found")
        print("Please install requirements: pip install -r requirements_new.txt")
        return False

def main():
    if not check_requirements():
        sys.exit(1)
    
    print("Starting FastAPI Move Extended server...")
    print("Server will be available at: http://localhost:909")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start the FastAPI server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "909",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
