# STT/TTS-Only Backend Service

Minimal Cloud Run service that provides **only** Speech-to-Text and Text-to-Speech endpoints.

**Why this architecture?**
- **Gemini API** is called **directly from the browser** (user provides their API key)
- **STT/TTS** still need a backend (Google Cloud APIs require service account auth)
- This reduces backend complexity and cost

## Architecture

```
Browser (GitHub Pages)
├─→ Gemini API (direct) - User's API key
└─→ Cloud Run (STT/TTS only) - Service account auth
```

## Deployment

```bash
cd api/stt-tts-only
./deploy.sh
```

This will:
1. Build Docker image
2. Push to GCR
3. Deploy to Cloud Run
4. Print the service URL

## Endpoints

- `GET /health` - Health check
- `POST /api/stt` - Speech-to-Text (audio file → text)
- `POST /api/tts` - Text-to-Speech (text → audio MP3)

## Environment Variables

- `GOOGLE_CLOUD_PROJECT` - GCP project ID (default: terpedia-489015)

## Service Account

The Cloud Run service needs a service account with:
- Cloud Speech Client
- Cloud Text-to-Speech Client

Set via IAM or during deployment.
