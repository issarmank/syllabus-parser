# app/services/pdf_reader.py
from io import BytesIO
from typing import Optional
from pypdf import PdfReader
from fastapi import UploadFile

def extract_text_from_pdf(data: bytes, max_pages: Optional[int] = None) -> str:
    reader = PdfReader(BytesIO(data))
    total = len(reader.pages)
    limit = min(total, max_pages) if max_pages else total
    parts = []
    for i in range(limit):
        page = reader.pages[i]
        text = page.extract_text() or ""
        parts.append(text.strip())
    return "\n\n".join(parts).strip()
