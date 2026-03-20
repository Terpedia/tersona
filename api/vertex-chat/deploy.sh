#!/bin/bash
# Deploy TerpeneQueen Vertex AI Chat API to Cloud Run

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-terpedia-489015}"
REGION="${GOOGLE_LOCATION:-us-central1}"
SERVICE_NAME="terpenequeen-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building and deploying ${SERVICE_NAME} to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"

# Build and push Docker image
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_LOCATION=${REGION},DEFAULT_TTS_VOICE=en-US-Neural2-F" \
  --service-account $(gcloud iam service-accounts list --project ${PROJECT_ID} --filter="displayName:librechat-speech" --format="value(email)" | head -1 || echo "")

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID} --format="value(status.url)")

echo ""
echo "✅ Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Update docs/index.html with this URL, or set it in localStorage as 'api_url'"
