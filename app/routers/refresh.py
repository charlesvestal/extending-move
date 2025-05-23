"""
Refresh router - handles library refresh functionality
"""
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from core.refresh_handler import refresh_library

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/refresh", response_class=HTMLResponse)
async def get_refresh_form(request: Request):
    """Get the refresh form."""
    return templates.TemplateResponse(
        "components/refresh.html", 
        {"request": request}
    )

@router.post("/refresh", response_class=HTMLResponse)
async def process_refresh(request: Request, action: str = Form(...)):
    """Process library refresh."""
    if action != "refresh_library":
        return templates.TemplateResponse(
            "components/refresh.html",
            {
                "request": request,
                "message": "Invalid action",
                "message_type": "error"
            }
        )
    
    try:
        success, message = refresh_library()
        message_type = "success" if success else "error"
        
        return templates.TemplateResponse(
            "components/refresh.html",
            {
                "request": request,
                "message": message,
                "message_type": message_type
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "components/refresh.html",
            {
                "request": request,
                "message": f"Error refreshing library: {str(e)}",
                "message_type": "error"
            }
        )
