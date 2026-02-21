import os
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Zoom録画分析", version="0.1.0")

# CORS（開発用。必要なら後で絞る）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# frontend を /static で配信（/static/upload.js など）
# ※frontend フォルダが存在する前提
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    # http://localhost:8000/ で frontend/index.html を返す
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    # アップロードされたファイルを backend/uploads/ に保存するだけ（まず動作確認）
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return JSONResponse(
        {
            "status": "success",
            "filename": file.filename,
            "saved_path": save_path,
        }
    )