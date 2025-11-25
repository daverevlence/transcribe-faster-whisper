import json
import uuid
import datetime
import tempfile
import boto3
from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel

app = FastAPI()

# DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-2")
table = dynamodb.Table("revlence-transcriptions")

# Load model once at container start
model = WhisperModel("medium", device="cpu")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Save uploaded audio temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        audio_path = tmp.name

    # Run faster-whisper
    segments, info = model.transcribe(audio_path)

    # Build transcription text
    text_output = " ".join([segment.text for segment in segments])

    # Full payload (segments + metadata)
    payload = {
        "detected_language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "segments": [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text
            }
            for s in segments
        ],
        "full_text": text_output
    }

    # Create UUID
    record_id = str(uuid.uuid4())

    # Prepare DynamoDB item
    item = {
        "uuid": record_id,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "payload": json.dumps(payload),
    }

    # Save to DynamoDB
    table.put_item(Item=item)

    # Return response
    return {
        "uuid": record_id,
        "text": text_output,
        "payload_saved": True
    }
