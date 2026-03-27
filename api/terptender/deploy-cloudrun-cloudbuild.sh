#!/usr/bin/env bash
# Deploy TerpTender to Cloud Run (Cloud Build). Same project/SA pattern as gemini-proxy.
# Usage: from this directory: bash deploy-cloudrun-cloudbuild.sh

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-terpedia-489015}"
REGION="${GOOGLE_LOCATION:-us-central1}"
SERVICE_NAME="terptender"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building TerpTender image and deploying to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

gcloud builds submit --tag "$IMAGE_NAME" --project "$PROJECT_ID" .

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --allow-unauthenticated \
  --service-account "terpenequeen-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --memory 512Mi \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_LOCATION=$REGION" \
  --port 8080

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format 'value(status.url)')

echo ""
echo "Deployment complete."
echo "Service URL: $SERVICE_URL"
