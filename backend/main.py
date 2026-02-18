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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # backend/
PROJECT_DIR = os.path.dirname(BASE_DIR)                        # project root
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# frontend/ を静的配信（/script.js や /styles.css もここから配信される）
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

@app.get("/")
async def root():
    # StaticFiles(html=True)でもindexは返るけど明示しておくと安心
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

def _format_sec(sec: float) -> str:
    # 94.2秒 -> "94.2秒" / 135秒 -> "2分15秒" みたいな表記
    if sec < 60:
        return f"{sec:.1f}秒"
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}分{s}秒"

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # アップロード保存
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ---- v1: ここは“ダミー分析”でOK（UI作りのため）
    # 後でここを「音声抽出→VAD→話者分離→文字起こし」に差し替える
    duration_sec = 54 * 60 + 44  # 54分44秒（例）
    coach_ratio = 14.8
    student_ratio = 85.2

    # ダミーのタイムライン（あとで実データに置換）
    timeline = [
        {"start": 62.0, "end": 71.0, "speaker": "coach", "text": "こんにちは。よろしくお願いします。マイクオンになりました。", "tags": []},
        {"start": 71.0, "end": 75.1, "speaker": "student", "text": "はい。よろしくお願いします。", "tags": []},
        {"start": 76.0, "end": 80.7, "speaker": "coach", "text": "東京は雪で大騒ぎでしたけど、大阪降りました？", "tags": ["question"]},
        {"start": 80.7, "end": 92.1, "speaker": "student", "text": "いや、もう全然。もうチラリみたいな雪。", "tags": []},
        {"start": 117.0, "end": 211.2, "speaker": "coach", "text": "（長めに説明…）", "tags": ["long_talk"]},
    ]

    longest_monologue_sec = 94.2
    silence_count = 8
    silence_avg_sec = 8.9

    # スコアも“根拠数”を返す（あとで実検出に置換）
    scores = {
        "empathy":   {"score": 5, "out_of": 5, "evidence": 12},
        "approval":  {"score": 3, "out_of": 5, "evidence": 6},
        "question":  {"score": 3, "out_of": 5, "evidence": 60},
        "silence":   {"score": 4, "out_of": 5, "evidence": silence_count},
        "listening": {"score": 4, "out_of": 5, "evidence": 18},
    }

    actions = [
        f"最長発話が{_format_sec(longest_monologue_sec)}（話しすぎ）: 30秒を目安に「どう思いますか？」で問いを返しましょう。",
        f"発話バランスが良好（受講生{student_ratio:.1f}%）: 受講生が十分に話せる環境が作れています。",
    ]

    return {
        "file_name": file.filename,
        "duration_sec": duration_sec,
        "summary": {
            "coach_ratio": coach_ratio,
            "student_ratio": student_ratio,
            "coach_turns": 108,
            "student_turns": 705,
            "longest_monologue_sec": longest_monologue_sec,
            "silence_count": silence_count,
            "silence_avg_sec": silence_avg_sec,
        },
        "scores": scores,
        "actions": actions,
        "timeline": timeline,
        "debug": {
            "saved_path": file_path
        }
    }
