#!/usr/bin/env bash
# Deploy STT/TTS service using local Docker build (avoids Cloud Build permissions)
# Requires: Docker installed and authenticated with GCR

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-terpedia-489015}"
REGION="${GOOGLE_LOCATION:-us-central1}"
SERVICE_NAME="stt-tts-service"

echo "Deploying STT/TTS service to Cloud Run (local build)..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Authenticate Docker with GCR
echo "Authenticating Docker with GCR..."
gcloud auth configure-docker gcr.io --quiet

# Build Docker image locally
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
echo "Building Docker image locally: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

# Push to GCR
echo ""
echo "Pushing image to GCR..."
docker push "$IMAGE_NAME"

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
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --service-account "terpenequeen-api@terpedia-489015.iam.gserviceaccount.com" 2>/dev/null || \
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
echo "Update your frontend to use this URL for STT/TTS API calls"
