from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.get("/")
def index():
    return {"message": "Hello from FastAPI"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    return {"filename": file.filename, "size": len(data)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)