# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import syllabus

app = FastAPI(title="Syllabus Parser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Syllabus Parser API", "endpoints": ["/health", "/upload", "/parse-syllabus"]}

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(syllabus.router)
