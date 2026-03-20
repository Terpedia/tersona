# TerpeneQueen Vertex AI Chat API

Cloud Run service providing:
- **Vertex AI Gemini** chat with TerpeneQueen persona
- **Google Cloud Speech-to-Text** (STT)
- **Google Cloud Text-to-Speech** (TTS)
- **Complete audio chat** endpoint (STT → AI → TTS)

## Prerequisites

1. **GCP Project** with billing enabled
2. **APIs enabled**:
   ```bash
   gcloud services enable aiplatform.googleapis.com \
     speech.googleapis.com \
     texttospeech.googleapis.com \
     cloudbuild.googleapis.com \
     run.googleapis.com \
     --project terpedia-489015
   ```
3. **Service Account** with roles:
   - Vertex AI User
   - Cloud Speech Client
   - Cloud Text-to-Speech Client
   - Service Account Token Creator (for Cloud Run)

## Deployment

### Quick Deploy

```bash
cd api/vertex-chat
chmod +x deploy.sh
./deploy.sh
```

This will:
1. Build Docker image
2. Push to GCR
3. Deploy to Cloud Run
4. Print the service URL

### Manual Deploy

```bash
# Set variables
export GOOGLE_CLOUD_PROJECT=terpedia-489015
export GOOGLE_LOCATION=us-central1

# Build and push
gcloud builds submit --tag gcr.io/${GOOGLE_CLOUD_PROJECT}/terpenequeen-api

# Deploy
gcloud run deploy terpenequeen-api \
  --image gcr.io/${GOOGLE_CLOUD_PROJECT}/terpenequeen-api \
  --platform managed \
  --region ${GOOGLE_LOCATION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_LOCATION=${GOOGLE_LOCATION}"
```

## Service Account Setup

The Cloud Run service needs a service account with the required permissions:

```bash
# Create or use existing service account
SERVICE_ACCOUNT="librechat-speech@terpedia-489015.iam.gserviceaccount.com"

# Grant roles
gcloud projects add-iam-policy-binding terpedia-489015 \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding terpedia-489015 \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/speech.client"

gcloud projects add-iam-policy-binding terpedia-489015 \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudtts.client"
```

Then deploy with:
```bash
gcloud run deploy terpenequeen-api \
  --service-account ${SERVICE_ACCOUNT} \
  # ... other flags
```

## API Endpoints

### `POST /api/chat`
Text chat with TerpeneQueen.

**Request:**
```json
{
  "message": "What are terpenes?",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! I'm TerpeneQueen..."}
  ]
}
```

**Response:**
```json
{
  "response": "Terpenes are aromatic compounds...",
  "conversation_history": [...]
}
```

### `POST /api/stt`
Speech-to-text conversion.

**Request:** Multipart form with `file` (audio) and `language` (optional, default: "en-US")

**Response:**
```json
{
  "text": "transcribed text",
  "language": "en-US"
}
```

### `POST /api/tts`
Text-to-speech synthesis.

**Request:** Form data with `text`, `voice` (optional, default: "susan"), `speed` (optional, default: 1.0)

**Response:** MP3 audio file

### `POST /api/chat-audio`
Complete audio chat: STT → AI → TTS.

**Request:** Multipart form with:
- `audio_file`: Audio recording
- `conversation_history`: JSON string (optional)
- `language`: Language code (optional, default: "en-US")

**Response:** MP3 audio file with headers:
- `X-User-Transcript`: Transcribed user message
- `X-Assistant-Text`: AI response text

## Environment Variables

- `GOOGLE_CLOUD_PROJECT`: GCP project ID (default: terpedia-489015)
- `GOOGLE_LOCATION`: Region for Vertex AI (default: us-central1)
- `DEFAULT_TTS_VOICE`: Default TTS voice (default: en-US-Neural2-F)
- `CUSTOM_VOICE_NAME`: Susan Trapp's custom voice name (when available)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/auth.json

# Run locally
uvicorn main:app --host 0.0.0.0 --port 8080
```

## Frontend Integration

Update `docs/index.html` with your Cloud Run service URL:

```javascript
const API_BASE_URL = 'https://terpenequeen-api-xxx.run.app';
```

Or let users enter it in the UI (stored in localStorage).
