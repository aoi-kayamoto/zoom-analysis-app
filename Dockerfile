FROM python:3.11-slim

# ffmpeg (Whisperに必要)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# backend配下のコードをコンテナ直下にコピー
COPY backend/ /app/

# 依存関係
RUN pip install --no-cache-dir -r requirements.txt

# Renderが渡すPORTで起動
CMD ["bash", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]FROM python:3.10-slim

WORKDIR /app

COPY backend /app/backend

RUN pip install --upgrade pip
RUN pip install fastapi uvicorn openai

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
