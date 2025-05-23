# Move Extended - FastAPI Version

This is a modernized version of the Move Extended webserver using FastAPI, HTMX, and a component-based architecture.

## What's New

### Architecture Improvements
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **HTMX**: Dynamic content loading without full page refreshes
- **Component-based Templates**: Modular, reusable template components
- **Structured Routing**: Clean separation of concerns with dedicated routers
- **Better Error Handling**: Comprehensive error handling and user feedback

### User Experience Improvements
- **Single Page Application**: All tools accessible from one page with tabs
- **Real-time Loading**: Visual feedback during processing
- **Better Form Handling**: Improved form validation and submission
- **Responsive Design**: Better mobile and tablet support

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_new.txt
   ```

2. **Start the Server**:
   ```bash
   python start_fastapi.py
   ```
   
   Or directly with uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 909 --reload
   ```

3. **Access the Application**:
   Open http://localhost:909 in your browser

## Project Structure

```
├── main.py                     # FastAPI application entry point
├── start_fastapi.py           # Simple startup script
├── requirements_new.txt       # FastAPI dependencies
├── app/                       # Application package
│   ├── __init__.py
│   └── routers/              # API route handlers
│       ├── __init__.py
│       ├── refresh.py        # Library refresh functionality
│       ├── reverse.py        # WAV file reversal
│       ├── restore.py        # Move Set restoration
│       ├── slice_router.py   # Audio slicing
│       ├── drum_rack.py      # Drum rack inspector
│       ├── synth_preset.py   # Synth preset inspector
│       └── chord.py          # Chord kit generation
├── templates/                # Jinja2 templates
│   ├── base.html            # Base template with common elements
│   ├── index.html           # Main dashboard page
│   └── components/          # Reusable template components
│       ├── refresh.html
│       ├── reverse.html
│       ├── restore.html
│       ├── slice.html
│       ├── chord.html
│       ├── drum_rack_inspector.html
│       └── synth_preset_inspector.html
├── static/                  # Static assets (CSS, JS, images)
└── core/                   # Existing core functionality (unchanged)
```

## Key Features

### 1. Modern Web Technologies
- **FastAPI**: Automatic API documentation at `/docs`
- **HTMX**: Dynamic content loading with minimal JavaScript
- **Jinja2**: Powerful templating engine
- **Component Architecture**: Reusable, maintainable templates

### 2. Improved User Interface
- **Tabbed Interface**: All tools accessible from one page
- **Loading Indicators**: Visual feedback during processing
- **Better Error Messages**: Clear, actionable error reporting
- **Responsive Design**: Works on desktop, tablet, and mobile

### 3. Enhanced Developer Experience
- **Hot Reload**: Automatic server restart during development
- **Type Hints**: Better code completion and error detection
- **Structured Code**: Clear separation of concerns
- **Easy Testing**: Built-in testing support with FastAPI

## API Endpoints

All endpoints are prefixed with `/api`:

- `GET/POST /api/refresh` - Library refresh functionality
- `GET/POST /api/reverse` - WAV file reversal
- `GET/POST /api/restore` - Move Set restoration
- `GET/POST /api/slice` - Audio slicing
- `GET/POST /api/drum-rack` - Drum rack inspector
- `GET/POST /api/synth-preset` - Synth preset inspector
- `GET /api/chord` - Chord kit generation (client-side processing)

## Migration from Flask Version

The FastAPI version maintains compatibility with all existing core functionality:

- All existing handlers in `core/` and `handlers/` are preserved
- Same audio processing capabilities
- Same file formats and outputs
- Same Move device integration

### Key Differences
1. **URL Structure**: API endpoints now use `/api/` prefix
2. **Form Handling**: Improved with FastAPI's automatic validation
3. **File Uploads**: Better handling of multipart form data
4. **Error Responses**: More structured error information

## Development

### Adding New Tools
1. Create a new router in `app/routers/`
2. Create a corresponding template component in `templates/components/`
3. Add the router to `main.py`
4. Add a tab button in `templates/index.html`

### Customizing Templates
- Modify `templates/base.html` for site-wide changes
- Edit component templates in `templates/components/` for tool-specific changes
- Update CSS in `static/style.css`

### Testing
```bash
# Install test dependencies
pip install pytest httpx

# Run tests (when test suite is added)
pytest
```

## Deployment

### Development
```bash
python start_fastapi.py
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 909 --workers 4
```

### Docker (Future)
A Dockerfile will be provided for containerized deployment.

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements_new.txt`

2. **Port Already in Use**: If port 909 is busy, modify the port in `main.py` or `start_fastapi.py`

3. **Template Not Found**: Ensure template files are in the correct `templates/` directory structure

4. **Static Files Not Loading**: Check that `static/` directory contains all required CSS/JS files

### Debug Mode
Start with `--reload` flag for automatic reloading during development:
```bash
uvicorn main:app --host 0.0.0.0 --port 909 --reload --log-level debug
```

## Future Enhancements

- [ ] Complete drum rack inspector integration
- [ ] Full synth preset inspector functionality  
- [ ] WebSocket support for real-time progress updates
- [ ] User authentication and sessions
- [ ] API rate limiting
- [ ] Comprehensive test suite
- [ ] Docker containerization
- [ ] Database integration for user preferences

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Same license as the original Move Extended project.
