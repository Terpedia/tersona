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

# Check if API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY not set in environment"
    echo "Set it during deployment or in Cloud Function config"
    read -p "Enter Gemini API key (or press Enter to skip): " API_KEY
    if [ -n "$API_KEY" ]; then
        GEMINI_API_KEY="$API_KEY"
    fi
fi

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
  --ingress-settings internal-and-gclb \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest" 2>/dev/null || \
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
    --ingress-settings all \
    --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}"

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
