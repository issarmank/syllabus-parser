# app/main.py
from fastapi import FastAPI
from app.routes import syllabus

app = FastAPI(title="Syllabus Parser API")

app.include_router(syllabus.router)
