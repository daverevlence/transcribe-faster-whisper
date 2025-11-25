Faster Whisper - Revlence

Deploy as follows:

docker build -t faster-whisper-api .

aws ecr create-repository --repository-name faster-whisper-api --profile revlence

docker tag faster-whisper-api:latest 014822894558.dkr.ecr.ap-southeast-2.amazonaws.com/faster-whisper-api:latest

aws ecr get-login-password --profile revlence | docker login --username AWS --password-stdin 014822894558.dkr.ecr.ap-southeast-2.amazonaws.com

docker push 014822894558.dkr.ecr.ap-southeast-2.amazonaws.com/faster-whisper-api:latest
