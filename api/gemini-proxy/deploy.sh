#!/usr/bin/env bash
# Deploy Gemini API proxy as Cloud Function
# This keeps the API key secure on the server side

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-terpedia-489015}"
REGION="${GOOGLE_LOCATION:-us-central1}"
FUNCTION_NAME="gemini-proxy"

echo "Deploying Gemini API proxy to Cloud Functions..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# No API key needed - uses service account authentication
echo "✅ Using Vertex AI with service account (no API key needed)"

# Deploy Cloud Function
echo "Deploying Cloud Function..."
echo "Note: Function will only accept requests from tersona.terpedia.com"

gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --runtime python311 \
  --region "$REGION" \
  --source . \
  --entry-point chat \
  --trigger-http \
  --allow-unauthenticated \
  --project "$PROJECT_ID" \
  --memory 512MB \
  --timeout 60s \
  --max-instances 10 \
  --service-account "terpenequeen-api@terpedia-489015.iam.gserviceaccount.com" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_LOCATION=$REGION" \
  2>/dev/null || \
  gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source . \
    --entry-point chat \
    --trigger-http \
    --allow-unauthenticated \
    --project "$PROJECT_ID" \
    --memory 512MB \
    --timeout 60s \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_LOCATION=$REGION"

# Get function URL
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
  --gen2 \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format 'value(serviceConfig.uri)')

echo ""
echo "✅ Deployment complete!"
echo "Function URL: $FUNCTION_URL"
echo ""
echo "Update your frontend to use this URL for chat API calls"
echo "Example: ${FUNCTION_URL}/chat"
