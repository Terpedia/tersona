#!/usr/bin/env bash
# Deploy Terpene Chat API to Cloud Run
# Builds Docker image locally and pushes to GCR, then deploys to Cloud Run

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-terpedia-489015}"
REGION="${GOOGLE_LOCATION:-us-central1}"
SERVICE_NAME="gemini-proxy"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Deploying Terpene Chat API to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Build Docker image locally
echo "Building Docker image..."
docker build -t "$IMAGE_NAME" .

# Push to GCR
echo "Pushing image to GCR..."
docker push "$IMAGE_NAME"

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --allow-unauthenticated \
  --service-account "terpenequeen-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --memory 1Gi \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_LOCATION=$REGION" \
  --port 8080

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Endpoints:"
echo "  - Chat: ${SERVICE_URL}/chat"
echo "  - STT: ${SERVICE_URL}/stt"
echo "  - TTS: ${SERVICE_URL}/tts"
echo "  - Health: ${SERVICE_URL}/health"
echo ""
echo "Update your frontend to use this URL for all API calls"
