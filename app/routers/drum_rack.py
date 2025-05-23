"""
Drum Rack Inspector router - handles drum rack inspection functionality
"""
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from handlers.drum_rack_inspector_handler_class import DrumRackInspectorHandler

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/drum-rack", response_class=HTMLResponse)
async def get_drum_rack_form(request: Request):
    """Get the drum rack inspector form."""
    try:
        handler = DrumRackInspectorHandler()
        context = handler.handle_get()
        context["request"] = request
        
        return templates.TemplateResponse(
            "components/drum_rack_inspector.html",
            context
        )
    except Exception as e:
        return templates.TemplateResponse(
            "components/drum_rack_inspector.html",
            {
                "request": request,
                "message": f"Error loading drum rack inspector: {str(e)}",
                "message_type": "error"
            }
        )

@router.post("/drum-rack", response_class=HTMLResponse)
async def process_drum_rack(request: Request):
    """Process drum rack inspector actions."""
    # Create a mock form object from FastAPI form data
    form_data = await request.form()
    
    class MockForm:
        def __init__(self, form_data):
            self._data = dict(form_data)
        
        def getvalue(self, key, default=None):
            return self._data.get(key, default)
        
        def __contains__(self, key):
            return key in self._data
    
    try:
        mock_form = MockForm(form_data)
        handler = DrumRackInspectorHandler()
        result = handler.handle_post(mock_form)
        
        if result:
            result["request"] = request
            return templates.TemplateResponse(
                "components/drum_rack_inspector.html",
                result
            )
        else:
            return templates.TemplateResponse(
                "components/drum_rack_inspector.html",
                {
                    "request": request,
                    "message": "Processing completed",
                    "message_type": "success"
                }
            )
            
    except Exception as e:
        return templates.TemplateResponse(
            "components/drum_rack_inspector.html",
            {
                "request": request,
                "message": f"Error processing drum rack: {str(e)}",
                "message_type": "error"
            }
        )
