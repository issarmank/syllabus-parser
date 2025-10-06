# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import syllabus
from app.config import FRONTEND_ORIGIN

app = FastAPI(title="Syllabus Parser API")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if FRONTEND_ORIGIN:
    allowed_origins.append(FRONTEND_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://syllabus-parser.*\.vercel\.app$",  # allow previews
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

@app.get("/")
def root():
    return {"message": "Syllabus Parser API", "endpoints": ["/health", "/upload", "/parse-syllabus"]}

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(syllabus.router)
