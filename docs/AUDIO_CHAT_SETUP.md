# Audio Chat Setup — TerpeneQueen with Vertex AI + STT/TTS

Complete guide for setting up audio chat with TerpeneQueen using Google Vertex AI, Speech-to-Text, and Text-to-Speech.

## Architecture

```
GitHub Pages (Frontend)
    ↓
Cloud Run API (Backend)
    ↓
    ├─→ Vertex AI Gemini (Chat)
    ├─→ Cloud Speech-to-Text (STT)
    └─→ Cloud Text-to-Speech (TTS)
```

## Prerequisites

1. **GCP Project**: `terpedia-489015` (or your project)
2. **APIs Enabled**:
   ```bash
   gcloud services enable \
     aiplatform.googleapis.com \
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

## Step 1: Deploy Cloud Run API

### Option A: Using Deploy Script

```bash
cd api/vertex-chat
export GOOGLE_CLOUD_PROJECT=terpedia-489015
export GOOGLE_LOCATION=us-central1
./deploy.sh
```

### Option B: Using Terraform

```bash
cd api/vertex-chat
terraform init
terraform plan
terraform apply
```

### Option C: Manual gcloud

```bash
# Build and push
gcloud builds submit --tag gcr.io/terpedia-489015/terpenequeen-api

# Deploy
gcloud run deploy terpenequeen-api \
  --image gcr.io/terpedia-489015/terpenequeen-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=terpedia-489015,GOOGLE_LOCATION=us-central1"
```

After deployment, note the **service URL** (e.g., `https://terpenequeen-api-xxx.run.app`).

## Step 2: Update Frontend

### Option A: Hardcode API URL

Edit `docs/index.html` and update:

```javascript
const API_BASE_URL = 'https://terpenequeen-api-xxx.run.app'; // Your Cloud Run URL
```

### Option B: User-Entered URL (Current)

The frontend already supports entering the API URL in the UI. Users can:
1. Enter the Cloud Run URL when first loading the page
2. It's saved in localStorage
3. Or you can set a default in the code

## Step 3: Deploy Frontend to GitHub Pages

1. Commit and push:
   ```bash
   git add docs/ api/
   git commit -m "Add TerpeneQueen audio chat with Vertex AI"
   git push origin main
   ```

2. GitHub Actions will auto-deploy to Pages

3. Configure custom domain `tersona.terpedia.com` (see `DEPLOYMENT.md`)

## Step 4: Test Audio Chat

1. Visit `https://tersona.terpedia.com`
2. Enter your Cloud Run API URL (or use default if hardcoded)
3. Click **🎤 Voice** mode
4. Click the microphone button to record
5. Speak your question
6. Click again to stop
7. Wait for TerpeneQueen's audio response!

## Features

### Text Mode
- Type messages
- Get text + audio responses
- Full conversation history

### Voice Mode
- Record audio messages
- Automatic STT → AI → TTS pipeline
- Audio playback of responses
- Transcripts shown in chat

## Troubleshooting

### "Failed to get response" error

- Check Cloud Run service is running: `gcloud run services list`
- Verify service URL is correct
- Check Cloud Run logs: `gcloud run services logs read terpenequeen-api`

### Microphone not working

- Browser requires HTTPS (or localhost) for microphone access
- Check browser permissions for microphone
- Try a different browser

### Audio playback issues

- Check browser audio permissions
- Verify TTS endpoint returns MP3
- Check browser console for errors

### Service Account Permissions

If you see permission errors:

```bash
# Find your service account
SERVICE_ACCOUNT=$(gcloud run services describe terpenequeen-api \
  --region us-central1 \
  --format="value(spec.template.spec.serviceAccountName)")

# Grant missing roles
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

## Cost Considerations

- **Vertex AI**: Pay per token (generation)
- **Speech-to-Text**: Pay per 15-second increment
- **Text-to-Speech**: Pay per character
- **Cloud Run**: Pay per request + compute time

For low traffic, costs should be minimal. Monitor in GCP Console.

## Next Steps

- [ ] Train Susan Trapp's custom voice (see `deploy/librechat-gcp/docs/GOOGLE_VOICE_SUSAN_TRAPP.md`)
- [ ] Set `CUSTOM_VOICE_NAME` env var in Cloud Run
- [ ] Add podcast export feature
- [ ] Optimize audio quality settings
