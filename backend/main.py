from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/script.js")
async def script():
    return FileResponse(os.path.join(BASE_DIR, "script.js"))

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    return {"message": "ファイル受信成功"}
