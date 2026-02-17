import os
import gc
import re
import math
import tempfile
import subprocess
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Coach Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

def extract_audio(video_path: str, out_path: str):
    cmd = ["ffmpeg", "-y", "-i", video_path, "-ar", "16000", "-ac", "1", "-f", "wav", out_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg エラー: {result.stderr}")

def transcribe_audio(audio_path: str) -> list[dict]:
    from faster_whisper import WhisperModel
    model = None
    try:
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, info = model.transcribe(
            audio_path, language="ja", vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500}, beam_size=5,
        )
        return [{"start": round(s.start,2), "end": round(s.end,2), "text": s.text.strip(), "duration": round(s.end-s.start,2)} for s in segments]
    finally:
        del model
        gc.collect()

COACH_PATTERNS = re.compile(r'(どう|ですか|ましたか|ますか|ましょう|いかがですか|教えてください|なるほど|そうですね|おっしゃる|ありがとう|まず|確認|整理|どんな|どのよう|何が|誰が|いつ|どこで|なぜ|どれ)', re.IGNORECASE)

def assign_speakers(segments: list[dict]) -> list[dict]:
    labeled = []
    prev_speaker = "coach"
    for i, seg in enumerate(segments):
        text = seg["text"]
        coach_score = 0
        if COACH_PATTERNS.search(text): coach_score += 1
        if text.endswith("か") or text.endswith("か？") or text.endswith("?"): coach_score += 1
        if seg["duration"] > 40: coach_score -= 1
        if i == 0: speaker = "coach"
        elif prev_speaker == "coach": speaker = "coach" if coach_score >= 2 else "student"
        else: speaker = "coach" if coach_score >= 1 else "student"
        prev_speaker = speaker
        labeled.append({**seg, "speaker": speaker})
    return labeled

def calc_statistics(segments: list[dict]) -> dict:
    coach_segs   = [s for s in segments if s["speaker"] == "coach"]
    student_segs = [s for s in segments if s["speaker"] == "student"]
    coach_time   = sum(s["duration"] for s in coach_segs)
    student_time = sum(s["duration"] for s in student_segs)
    total_time   = coach_time + student_time or 1
    coach_pct    = round(coach_time / total_time * 100, 1)
    longest      = max((s["duration"] for s in segments), default=0)
    silences     = [round(segments[i]["start"] - segments[i-1]["end"], 1) for i in range(1, len(segments)) if segments[i]["start"] - segments[i-1]["end"] >= 3]
    avg_coach    = (coach_time / len(coach_segs)) if coach_segs else 0
    questions    = [s for s in coach_segs if re.search(r'[?？]|か[。　\s]?$', s["text"])]
    open_q       = len([q for q in questions if COACH_PATTERNS.search(q["text"])])
    return {
        "coach_pct": coach_pct, "student_pct": round(100 - coach_pct, 1),
        "coach_turns": len(coach_segs), "student_turns": len(student_segs),
        "longest_speech": round(longest, 1),
        "longest_speech_alert": "danger" if longest >= 60 else "warning" if longest >= 30 else "safe",
        "silence_count": len(silences), "silence_avg": round(sum(silences)/len(silences),1) if silences else 0,
        "avg_coach_duration": round(avg_coach, 1),
        "question_count": len(questions), "open_questions": open_q, "closed_questions": len(questions) - open_q,
    }

EMPATHY_WORDS  = re.compile(r'(なるほど|そうですね|わかります|大変でしたね|つらい|感じ|気持ち)')
APPROVAL_WORDS = re.compile(r'(いいですね|素晴らしい|よかった|できています|すごい|さすが|ありがとう)')

def calc_skill_scores(segments: list[dict], stats: dict) -> dict:
    coach_texts = " ".join(s["text"] for s in segments if s["speaker"] == "coach")
    empathy_score  = min(5, max(1, round(len(EMPATHY_WORDS.findall(coach_texts)) / 2)))
    approval_score = min(5, max(1, round(len(APPROVAL_WORDS.findall(coach_texts)) / 1.5)))
    open_ratio     = stats["open_questions"] / (stats["question_count"] or 1)
    question_score = min(5, max(1, round(open_ratio * 5)))
    silence_score  = min(5, max(1, math.ceil(stats["silence_count"] / 2)))
    listening_score= min(5, max(1, round(stats["student_pct"] / 20)))
    return {"empathy": empathy_score, "approval": approval_score, "question": question_score, "silence": silence_score, "listening": listening_score}

def generate_advice(stats: dict, scores: dict) -> list[dict]:
    advice = []
    if stats["longest_speech"] >= 60:
        advice.append({"level":"red","text":f"最長発話が{stats['longest_speech']}秒（🚨 話しすぎ）：30秒を目安に「どう思いますか？」と問いを返しましょう。"})
    elif stats["longest_speech"] >= 30:
        advice.append({"level":"amber","text":f"最長発話が{stats['longest_speech']}秒（⚠ 要注意）：受講生が考える余白を意識してください。"})
    if stats["coach_pct"] > 50:
        advice.append({"level":"amber","text":f"コーチ発話率が{stats['coach_pct']}%：理想は受講生が60〜70%話す状態です。「もう少し教えてください」を意識的に増やしましょう。"})
    else:
        advice.append({"level":"green","text":f"発話バランスが良好（受講生{stats['student_pct']}%）：受講生が十分に話せる環境を作れています。"})
    if scores["question"] <= 2:
        advice.append({"level":"amber","text":f"問いスコアが低め（★{scores['question']}）：「どんな気持ちでしたか？」などオープン質問を増やしましょう。"})
    if scores["approval"] >= 4:
        advice.append({"level":"green","text":f"承認スコアが良好（★{scores['approval']}）：受講生の発言を受け止め、承認する言葉が多く見られました。"})
    if stats["silence_count"] == 0:
        advice.append({"level":"amber","text":"沈黙がほとんどありません：意図的に2〜3秒待つことで、受講生が深く考える時間を作れます。"})
    return advice

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    allowed = {".mp4", ".mov", ".m4a", ".mp3", ".wav", ".webm"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"未対応の形式: {suffix}")
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"input{suffix}")
        with open(input_path, "wb") as f:
            f.write(await file.read())
        if suffix in {".mp4", ".mov", ".webm"}:
            audio_path = os.path.join(tmpdir, "audio.wav")
            extract_audio(input_path, audio_path)
        else:
            audio_path = input_path
        segments = transcribe_audio(audio_path)
        if not segments:
            raise HTTPException(422, "音声を検出できませんでした")
        segments = assign_speakers(segments)
        stats  = calc_statistics(segments)
        scores = calc_skill_scores(segments, stats)
        advice = generate_advice(stats, scores)
        total_sec = segments[-1]["end"] if segments else 0
    return {
        "filename": file.filename,
        "duration": f"{int(total_sec//60)}分{int(total_sec%60):02d}秒",
        "stats": stats, "scores": scores, "advice": advice,
        "segments": segments[:60],
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
