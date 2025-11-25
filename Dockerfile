FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Install dependencies
RUN pip install --no-cache-dir faster-whisper uvicorn fastapi

# Faster-whisper API server
WORKDIR /app
COPY app.py /app/app.py

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
