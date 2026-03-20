#!/usr/bin/env bash
# Deploy STT/TTS-only service to Cloud Run
# This is a minimal backend - Gemini API is called directly from the browser

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-terpedia-489015}"
REGION="${GOOGLE_LOCATION:-us-central1}"
SERVICE_NAME="stt-tts-service"

echo "Deploying STT/TTS service to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Build and push Docker image
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
echo "Building Docker image: $IMAGE_NAME"
gcloud builds submit --tag "$IMAGE_NAME" --project "$PROJECT_ID" .

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Update your frontend to use:"
echo "  - Gemini API: Direct from browser (user provides API key)"
echo "  - STT/TTS API: $SERVICE_URL"
