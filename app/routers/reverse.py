"""
Reverse router - handles WAV file reversal functionality
"""
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from core.reverse_handler import get_wav_files, reverse_wav_file

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/reverse", response_class=HTMLResponse)
async def get_reverse_form(request: Request):
    """Get the reverse form with available WAV files."""
    try:
        wav_files = get_wav_files("/data/UserData/UserLibrary/Samples")
        options_html = ""
        for wav_file in wav_files:
            options_html += f'<option value="{wav_file}">{wav_file}</option>'
        
        return templates.TemplateResponse(
            "components/reverse.html",
            {
                "request": request,
                "options": options_html
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "components/reverse.html",
            {
                "request": request,
                "message": f"Error loading WAV files: {str(e)}",
                "message_type": "error",
                "options": ""
            }
        )

@router.post("/reverse", response_class=HTMLResponse)
async def process_reverse(request: Request, action: str = Form(...), filename: str = Form(...)):
    """Process WAV file reversal."""
    if action != "reverse":
        return templates.TemplateResponse(
            "components/reverse.html",
            {
                "request": request,
                "message": "Invalid action",
                "message_type": "error",
                "options": ""
            }
        )
    
    try:
        # Process the reversal
        success, message = reverse_wav_file(filename, "/data/UserData/UserLibrary/Samples")
        message_type = "success" if success else "error"
        
        # Reload WAV files for the form
        wav_files = get_wav_files("/data/UserData/UserLibrary/Samples")
        options_html = ""
        for wav_file in wav_files:
            selected = 'selected' if wav_file == filename else ''
            options_html += f'<option value="{wav_file}" {selected}>{wav_file}</option>'
        
        return templates.TemplateResponse(
            "components/reverse.html",
            {
                "request": request,
                "message": message,
                "message_type": message_type,
                "options": options_html
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "components/reverse.html",
            {
                "request": request,
                "message": f"Error reversing file: {str(e)}",
                "message_type": "error",
                "options": ""
            }
        )
