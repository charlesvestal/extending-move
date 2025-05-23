"""
Synth Preset Inspector router - handles synth preset inspection functionality
"""
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from handlers.synth_preset_inspector_handler_class import SynthPresetInspectorHandler

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/synth-preset", response_class=HTMLResponse)
async def get_synth_preset_form(request: Request):
    """Get the synth preset inspector form."""
    try:
        handler = SynthPresetInspectorHandler()
        context = handler.handle_get()
        context["request"] = request
        
        return templates.TemplateResponse(
            "components/synth_preset_inspector.html",
            context
        )
    except Exception as e:
        return templates.TemplateResponse(
            "components/synth_preset_inspector.html",
            {
                "request": request,
                "message": f"Error loading synth preset inspector: {str(e)}",
                "message_type": "error"
            }
        )

@router.post("/synth-preset", response_class=HTMLResponse)
async def process_synth_preset(request: Request):
    """Process synth preset inspector actions."""
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
        handler = SynthPresetInspectorHandler()
        result = handler.handle_post(mock_form)
        
        if result:
            result["request"] = request
            return templates.TemplateResponse(
                "components/synth_preset_inspector.html",
                result
            )
        else:
            return templates.TemplateResponse(
                "components/synth_preset_inspector.html",
                {
                    "request": request,
                    "message": "Processing completed",
                    "message_type": "success"
                }
            )
            
    except Exception as e:
        return templates.TemplateResponse(
            "components/synth_preset_inspector.html",
            {
                "request": request,
                "message": f"Error processing synth preset: {str(e)}",
                "message_type": "error"
            }
        )
