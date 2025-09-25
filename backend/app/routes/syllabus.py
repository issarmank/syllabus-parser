# app/routes/syllabus.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_reader import extract_text_from_pdf_bytes
from app.services.syllabus_parser import parse_syllabus
from app.models import EventsResponse

router = APIRouter()

@router.post("/parse-syllabus", response_model=EventsResponse)
async def parse_syllabus_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    pdf_bytes = await file.read()
    text = extract_text_from_pdf_bytes(pdf_bytes)
    return await parse_syllabus(text)

@router.post("/upload", response_model=EventsResponse)
async def upload_alias(file: UploadFile = File(...)):
    return await parse_syllabus_pdf(file)
