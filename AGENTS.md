# AGENTS.md - Project Context & Status

## Project Overview

**Extending Move** is a web-based tool suite for Ableton Move that provides advanced audio processing capabilities. We successfully migrated from a Flask-based architecture to a modern FastAPI-based architecture with improved modularity and maintainability.

## Current Status: ✅ MAJOR MIGRATION COMPLETED

### 🎉 Successfully Deployed FastAPI Version
- **Server Location**: `move.local:909` (Ableton Move device)
- **Status**: Fully operational and tested
- **Deployment**: Automated via `./utility-scripts/update-fastapi-on-move.sh`

## Architecture Transformation

### Before: Flask Monolith
```
move-webserver.py (single file)
├── All routes in one file
├── Inline HTML generation
├── Mixed concerns
└── Difficult to maintain
```

### After: FastAPI Modular Architecture
```
main.py (FastAPI app)
├── app/routers/ (modular route handlers)
│   ├── refresh.py ✅
│   ├── reverse.py ✅
│   ├── restore.py ✅
│   ├── chord.py ✅
│   ├── slice_router.py ⚠️ (disabled - import issues)
│   ├── drum_rack.py ⚠️ (disabled - import issues)
│   └── synth_preset.py ⚠️ (disabled - import issues)
├── templates/components/ (reusable components)
├── handlers/ (business logic classes)
└── core/ (shared functionality)
```

## Working Features ✅

### 1. Refresh Library
- **Route**: `/refresh`
- **Status**: ✅ FULLY WORKING
- **Recent Fix**: Fixed form POST action from `/api/refresh` to `/refresh`
- **Functionality**: Successfully calls D-Bus to refresh Move's library cache
- **Testing**: Confirmed working via browser and server logs

### 2. Reverse Audio
- **Route**: `/reverse`
- **Status**: ✅ WORKING
- **Functionality**: Reverses audio files and places them in Move

### 3. Restore Move Set
- **Route**: `/restore`
- **Status**: ✅ WORKING
- **Functionality**: Restores .ablbundle files to Move Set slots

### 4. Chord Generator
- **Route**: `/chord`
- **Status**: ✅ WORKING
- **Functionality**: Generates chord progressions and exports to Move

## Disabled Features ⚠️

These routes are temporarily disabled due to import issues but the code is ready:

### 1. Slice Kit (`/slice`)
- **Issue**: Import path problems in handler
- **Files Ready**: `app/routers/slice_router.py`, `templates/components/slice.html`

### 2. Drum Rack Inspector (`/drum-rack-inspector`)
- **Issue**: Import path problems in handler
- **Files Ready**: `app/routers/drum_rack.py`, `templates/components/drum_rack_inspector.html`

### 3. Synth Preset Inspector (`/synth-preset-inspector`)
- **Issue**: Import path problems in handler
- **Files Ready**: `app/routers/synth_preset.py`, `templates/components/synth_preset_inspector.html`

## Key Technical Improvements

### 1. Enhanced Error Handling
- Comprehensive logging in `core/refresh_handler.py`
- Better subprocess management with timeouts
- Detailed error messages for debugging

### 2. Component-Based Templates
- Reusable HTML components in `templates/components/`
- Consistent styling and behavior
- Easier maintenance and updates

### 3. Modular Router Architecture
- Each feature in its own router file
- Clean separation of concerns
- Easy to add new features

### 4. Automated Deployment
- `update-fastapi-on-move.sh` script handles full deployment
- Automatic dependency installation
- Server restart management

## File Structure & Key Files

### Core Application Files
- `main.py` - FastAPI application entry point
- `start_fastapi.py` - Development server launcher
- `requirements_new.txt` - FastAPI dependencies

### Router Files (app/routers/)
- `refresh.py` - Library refresh functionality ✅
- `reverse.py` - Audio reversal ✅
- `restore.py` - Move Set restoration ✅
- `chord.py` - Chord generation ✅
- `slice_router.py` - Audio slicing ⚠️
- `drum_rack.py` - Drum rack inspection ⚠️
- `synth_preset.py` - Synth preset inspection ⚠️

### Handler Classes (handlers/)
- `base_handler.py` - Base class for all handlers
- `refresh_handler_class.py` - Refresh functionality
- `reverse_handler_class.py` - Audio reversal
- `restore_handler_class.py` - Move Set restoration
- `slice_handler_class.py` - Audio slicing
- `drum_rack_inspector_handler_class.py` - Drum rack inspection
- `synth_preset_inspector_handler_class.py` - Synth preset inspection

### Core Functions (core/)
- `refresh_handler.py` - D-Bus library refresh (enhanced with debugging)
- `reverse_handler.py` - Audio reversal logic
- `restore_handler.py` - Move Set restoration logic
- `slice_handler.py` - Audio slicing logic
- Other core handlers...

### Templates
- `templates/base.html` - Base template with navigation
- `templates/index.html` - Main dashboard
- `templates/components/` - Individual feature components

### Deployment & Utilities
- `utility-scripts/update-fastapi-on-move.sh` - Main deployment script
- `utility-scripts/restart-webserver.sh` - Server restart utility

## Recent Debugging & Fixes

### Refresh Functionality Issue (RESOLVED ✅)
**Problem**: Refresh button wasn't working
**Root Cause**: Form was POSTing to `/api/refresh` instead of `/refresh`
**Solution**: 
1. Updated `templates/components/refresh.html` form action
2. Enhanced `core/refresh_handler.py` with comprehensive logging
3. Confirmed D-Bus integration working correctly

**Evidence of Fix**:
- Server logs show: "Library refreshed successfully."
- Browser displays: "Library refreshed successfully."
- POST requests return 200 OK status

## Next Steps & Remaining Work

### Immediate Priority
1. **Fix Import Issues** - Re-enable slice, drum_rack, and synth_preset routes
   - Debug import paths in handler classes
   - Test each route individually
   - Update main.py to include all routers

### Medium Priority
2. **Navigation Enhancement** - Add refresh/navigation to main dashboard
3. **Error Handling** - Improve error messages across all routes
4. **Testing** - Comprehensive testing of all features

### Future Enhancements
5. **Performance Optimization** - Profile and optimize audio processing
6. **UI/UX Improvements** - Enhanced styling and user experience
7. **Additional Features** - Based on user feedback

## Development Environment

### Local Development
```bash
# Start development server
python start_fastapi.py

# Access at: http://localhost:8000
```

### Production Deployment
```bash
# Deploy to Move device
./utility-scripts/update-fastapi-on-move.sh

# Access at: http://move.local:909
```

### Server Management
```bash
# Check server status
ssh ableton@move.local "ps aux | grep uvicorn"

# View logs
ssh ableton@move.local "tail -f /tmp/fastapi-webserver.log"

# Restart server
./utility-scripts/restart-webserver.sh
```

## Technical Notes

### D-Bus Integration
- Successfully integrated with Move's D-Bus system
- Refresh command: `dbus-send --system --type=method_call --dest=com.ableton.move --print-reply /com/ableton/move/browser com.ableton.move.Browser.refreshCache`
- Confirmed working on Move device

### Audio Processing
- Uses librosa, soundfile, and audiotsm libraries
- Handles WAV file processing and manipulation
- Integrates with Move's file system structure

### Move Integration
- Files placed in appropriate Move directories
- Automatic library refresh after file operations
- Proper file naming and organization

## Troubleshooting

### Common Issues
1. **Import Errors**: Check Python path and module structure
2. **D-Bus Failures**: Ensure Move is running and D-Bus service is available
3. **File Permissions**: Verify write access to Move directories
4. **Server Not Starting**: Check port availability and dependencies

### Debug Commands
```bash
# Test D-Bus directly
ssh ableton@move.local "dbus-send --system --type=method_call --dest=com.ableton.move --print-reply /com/ableton/move/browser com.ableton.move.Browser.refreshCache"

# Check server logs
ssh ableton@move.local "tail -20 /tmp/fastapi-webserver.log"

# Test route directly
wget -O - http://move.local:909/refresh
```

---

**Last Updated**: May 23, 2025
**Status**: FastAPI migration completed, core features working, ready for final route fixes
**Next Session**: Focus on re-enabling disabled routes (slice, drum_rack, synth_preset)
