# app/services/pdf_reader.py
from pypdf import PdfReader
from fastapi import UploadFile

def extract_text_from_pdf(file: UploadFile) -> str:
    reader = PdfReader(file.file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text
