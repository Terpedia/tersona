# Google Speech Bridge for LibreChat

FastAPI service that provides OpenAI-compatible STT/TTS endpoints using Google Cloud Speech APIs.

## What it does

- **Speech-to-Text (STT)**: Mimics OpenAI Whisper API but uses Google Cloud Speech-to-Text
- **Text-to-Speech (TTS)**: Mimics OpenAI TTS API but uses Google Cloud Text-to-Speech
- **Custom voice support**: Can use Susan Trapp's custom Google voice for TTS

## Why this is needed

LibreChat's `librechat.yaml` only supports these TTS/STT providers natively:
- OpenAI (Whisper + TTS)
- Azure OpenAI
- ElevenLabs
- LocalAI

Google Cloud Speech is not directly supported. This bridge translates LibreChat's OpenAI-format requests to Google Cloud APIs.

## Endpoints

- `POST /v1/audio/transcriptions` - STT (OpenAI Whisper compatible)
- `POST /v1/audio/speech` - TTS (OpenAI TTS compatible)
- `GET /health` - Health check

## Environment variables

- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON (or use Application Default Credentials)
- `DEFAULT_TTS_VOICE` - Default Google voice (e.g., `en-US-Neural2-A`)
- `CUSTOM_VOICE_NAME` - Susan Trapp's custom voice name when available (e.g., `custom-susan-trapp-terpenequeen`)

## Voice mapping

OpenAI voice names are mapped to Google voices:
- `alloy` → `en-US-Neural2-A`
- `echo` → `en-US-Neural2-C`
- `nova` → `en-US-Neural2-F`
- `susan` → Custom voice (Susan Trapp's trained voice)

## Running locally

```bash
pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT=terpedia-489015
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Running in Docker

See docker-compose.yml in parent directory.

## LibreChat configuration

In `librechat.yaml`, configure speech to use this bridge:

```yaml
speech:
  tts:
    openai:
      apiKey: "dummy"  # Not used, but required by schema
      baseURL: "http://speech-bridge:8001/v1"
      model: "tts-1"
      voices: ["alloy", "nova", "susan"]
  stt:
    openai:
      apiKey: "dummy"
      baseURL: "http://speech-bridge:8001/v1"
      model: "whisper-1"
```

The bridge will intercept these requests and forward them to Google Cloud Speech APIs.
