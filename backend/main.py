from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI()

# CORS設定（フロントと接続するため）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATH = os.path.join(BASE_DIR, "..", "frontend", "index.html")


@app.get("/")
def read_index():
    return FileResponse(FRONTEND_PATH)


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # 今は簡易テスト版（まず確実に動かす）
    return {
        "coach_ratio": "40%",
        "student_ratio": "60%",
        "longest_speech": "45秒",
        "feedback": "受講生がしっかり話せています 👍"
    }
