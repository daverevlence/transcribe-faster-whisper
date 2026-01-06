import json
import uuid
import datetime
import tempfile
import boto3
from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel

app = FastAPI()

# AWS Clients
dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-2")
table = dynamodb.Table("revlence-transcriptions")

s3 = boto3.client("s3")
S3_BUCKET = "revlence-transcriptions"

# Load Whisper model on startup
model = WhisperModel("medium", device="cpu")


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Save uploaded audio temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        audio_path = tmp.name

    # ---------------------------------------------------------
    # Run Faster-Whisper with FULL timestamp + word alignment
    # ---------------------------------------------------------
    segment_gen, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        without_timestamps=False,   # forces segments
        vad_filter=False,           # prevents segment removal
        beam_size=5,                # required for alignment
        temperature=0               # improves alignment stability
    )

    # IMPORTANT: convert generator to list
    segments = list(segment_gen)

    # Build full text
    text_output = " ".join([seg.text for seg in segments])

    # Build word-level breakdown
    words_output = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                words_output.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end
                })

    # Build segment breakdown
    segment_output = [
        {
            "start": s.start,
            "end": s.end,
            "text": s.text
        }
        for s in segments
    ]

    # Build full transcription payload
    payload = {
        "detected_language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "segments": segment_output,
        "words": words_output,
        "full_text": text_output
    }

    # Generate primary UUID
    record_id = str(uuid.uuid4())

    # ---------------------------------------------------------
    # SAVE PAYLOAD TO S3
    # ---------------------------------------------------------
    s3_key = f"transcriptions/{record_id}.json"

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(payload),
        ContentType="application/json"
    )

    # ---------------------------------------------------------
    # SAVE METADATA TO DYNAMODB
    # ---------------------------------------------------------
    item = {
        "uuid": record_id,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "s3_key": s3_key
    }

    table.put_item(Item=item)

    # ---------------------------------------------------------
    # Response to client
    # ---------------------------------------------------------
    return {
        "uuid": record_id,
        "segments": segment_output,
        "words": words_output,
        "s3_key": s3_key,
        "payload_saved": True
    }
