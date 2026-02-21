import os
import uuid
import shutil
import subprocess
import asyncio
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import whisper

app = FastAPI()

# ========= 環境変数 =========
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base").strip()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "250"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "1"))

MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
sem = asyncio.Semaphore(CONCURRENCY)

# ========= フロント固定パス（Railway確定対応） =========
FRONTEND_DIR = "/app/frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# ========= 一時保存 =========
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ========= Whisperモデル読み込み =========
model = whisper.load_model(WHISPER_MODEL)


def require_token(request: Request):
    if not APP_PASSWORD:
        raise HTTPException(status_code=500, detail="APP_PASSWORD not set")

    token = request.headers.get("X-App-Token", "")
    if token != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")


def to_wav(input_path: str) -> str:
    wav_path = os.path.splitext(input_path)[0] + ".wav"
    cmd = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


async def save_upload(upload: UploadFile, dst_path: str):
    size = 0
    chunk_size = 1024 * 1024

    with open(dst_path, "wb") as f:
        while True:
            chunk = await upload.read(chunk_size)
            if not chunk:
                break

            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large (max {MAX_UPLOAD_MB}MB)"
                )

            f.write(chunk)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "model": WHISPER_MODEL,
        "max_upload_mb": MAX_UPLOAD_MB,
        "concurrency": CONCURRENCY,
    }


@app.post("/api/analyze")
async def analyze(request: Request, file: UploadFile = File(...)):
    require_token(request)

    async with sem:
        input_path: Optional[str] = None
        wav_path: Optional[str] = None

        try:
            ext = os.path.splitext(file.filename or "")[1].lower()
            if ext not in [".mp4", ".m4a", ".mp3", ".wav", ".mov"]:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            temp_id = str(uuid.uuid4())
            input_path = os.path.join(UPLOAD_DIR, f"{temp_id}{ext}")

            await save_upload(file, input_path)

            wav_path = to_wav(input_path)

            result = model.transcribe(wav_path, fp16=False)
            text = (result.get("text") or "").strip()

            return JSONResponse({
                "ok": True,
                "text": text
            })

        except HTTPException as e:
            return JSONResponse({
                "ok": False,
                "error": e.detail
            }, status_code=e.status_code)

        except Exception as e:
            return JSONResponse({
                "ok": False,
                "error": str(e)
            }, status_code=500)

        finally:
            for p in [wav_path, input_path]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass