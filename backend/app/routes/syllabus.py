# app/routes/syllabus.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.syllabus_parser import parse_syllabus_from_pdf
from app.models import ParseResult

router = APIRouter()

@router.post("/parse-syllabus", response_model=ParseResult)
async def parse_syllabus_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    pdf_bytes = await file.read()
    return parse_syllabus_from_pdf(pdf_bytes)

@router.post("/upload", response_model=ParseResult)
async def upload_alias(file: UploadFile = File(...)):
    return await parse_syllabus_pdf(file)
