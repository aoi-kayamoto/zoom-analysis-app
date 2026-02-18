from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
import os
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ここはダミー（まずは動作確認）
    return {
        "file_name": file.filename,
        "duration_sec": 3600,
        "summary": {
            "coach_ratio": 40,
            "student_ratio": 60,
            "coach_turns": 120,
            "student_turns": 300,
            "longest_monologue_sec": 45,
            "silence_count": 6,
            "silence_avg_sec": 5.2
        },
        "scores": {
            "empathy": {"score": 4, "out_of": 5, "evidence": 10},
            "approval": {"score": 3, "out_of": 5, "evidence": 5},
            "question": {"score": 4, "out_of": 5, "evidence": 20},
            "silence": {"score": 4, "out_of": 5, "evidence": 6},
            "listening": {"score": 4, "out_of": 5, "evidence": 15}
        },
        "actions": ["話しすぎを30秒以内に抑えましょう"],
        "timeline": []
    }
