# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "extending-move" - a companion webserver for the Ableton Move device that provides advanced editing capabilities through a web interface at `move.local:909`. It allows users to manage presets, edit parameters, create chord/sliced kits, inspect drum racks, and manipulate Move sets with features not available in the default Move interface.

## Development Commands

### Running the Server
```bash
python3 move-webserver.py
```

### Testing
```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/test_file_name.py

# Run tests with verbose output
python3 -m pytest -v tests/
```

### Development Scripts
```bash
# Development mode with auto-restart
./utility-scripts/dev.sh

# Restart webserver
./utility-scripts/restart-webserver.sh

# Update from GitHub
./utility-scripts/update-on-move.sh
```

### Installing Dependencies
```bash
pip3 install -r requirements.txt
```

## Architecture Overview

### Core Structure
- **move-webserver.py**: Main Flask application entry point
- **core/**: Core business logic modules for different operations
- **handlers/**: Flask route handlers (class-based) that interface with core modules
- **static/**: JavaScript files for frontend functionality
- **templates_jinja/**: HTML templates using Jinja2
- **tests/**: Comprehensive test suite

### Key Components

#### Handler Pattern
The codebase uses a dual-layer handler pattern:
1. **Core handlers** (`core/`): Pure business logic functions
2. **Flask handlers** (`handlers/`): Class-based wrappers that handle HTTP requests/responses

Example: `core/restore_handler.py` contains the restore logic, while `handlers/restore_handler_class.py` handles the Flask routes.

#### Major Features
- **Set Management**: Upload/restore Ableton sets to Move pads with custom colors
- **Preset Editors**: Advanced parameter editing for Drift, Wavetable, and melodicSampler instruments
- **Kit Creation**: Chord kit generation and visual sample slicing tools  
- **Audio Processing**: Sample reversal, time stretching using RubberBand
- **MIDI Support**: Import MIDI files to create new sets

#### Configuration
- `core/config.py`: Centralized paths and constants for Move device integration
- Device paths target `/data/UserData/UserLibrary/` on the Move

#### Frontend
JavaScript modules handle real-time parameter visualization, audio preview, and interactive editing interfaces. The frontend uses Web Audio API for audio processing and custom knob/slider controls.

## Development Notes

### Testing Approach
- Comprehensive test coverage in `tests/` directory
- Tests cover both core logic and Flask route handlers
- Use pytest for running tests

### Audio Dependencies
- Requires `pyrubberband` for time stretching
- Uses `librosa` and `soundfile` for audio processing
- `mido` for MIDI file handling

### Device Integration
The server is designed to run directly on the Ableton Move device alongside the official Move server, accessing the device's file system for set and sample management.