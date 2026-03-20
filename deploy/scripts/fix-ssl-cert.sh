#!/usr/bin/env bash
# Fix SSL certificate for chat.tersona.terpedia.com
# Run: ./deploy/scripts/fix-ssl-cert.sh

set -e

PROJECT="terpedia-489015"
DOMAIN="chat.tersona.terpedia.com"

echo "=========================================="
echo "Fix SSL Certificate"
echo "=========================================="
echo "Project: $PROJECT"
echo "Domain: $DOMAIN"
echo ""

gcloud config set project $PROJECT

echo "1. Deleting old SSL certificate..."
gcloud compute ssl-certificates delete librechat-ssl-cert --global --quiet || echo "Certificate already deleted or doesn't exist"
echo ""

echo "2. Creating new SSL certificate..."
gcloud compute ssl-certificates create librechat-ssl-cert \
  --domains=$DOMAIN \
  --global
echo ""

echo "3. Checking certificate status..."
gcloud compute ssl-certificates describe librechat-ssl-cert --global
echo ""

echo "=========================================="
echo "SSL Certificate Recreation Complete"
echo "=========================================="
echo ""
echo "The certificate will provision in 15-60 minutes."
echo "Check status with:"
echo "  gcloud compute ssl-certificates describe librechat-ssl-cert --global"
echo ""
echo "Once status shows ACTIVE, the site will be accessible at:"
echo "  https://chat.tersona.terpedia.com"
echo ""
