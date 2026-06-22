from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from app.services.parser import extract_text_from_pdf

router = APIRouter(prefix="/bills", tags=["bills"])

@router.post("/upload", response_class=HTMLResponse)
async def upload_bill(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    text = extract_text_from_pdf(content)
    return HTMLResponse(content="<div class='loading'>Processing uploaded bill...</div>")
