#!/usr/bin/env bash
# Recreate SSL certificate by temporarily detaching from proxy
# Run: ./deploy/scripts/recreate-ssl-cert.sh

set -e

PROJECT="terpedia-489015"
DOMAIN="chat.tersona.terpedia.com"

echo "=========================================="
echo "Recreate SSL Certificate"
echo "=========================================="
echo "Project: $PROJECT"
echo "Domain: $DOMAIN"
echo ""

gcloud config set project $PROJECT

echo "Step 1: Create new SSL certificate with different name..."
gcloud compute ssl-certificates create librechat-ssl-cert-new \
  --domains=$DOMAIN \
  --global
echo ""

echo "Step 2: Update HTTPS proxy to use new certificate..."
gcloud compute target-https-proxies update librechat-https-proxy \
  --ssl-certificates=librechat-ssl-cert-new \
  --global
echo ""

echo "Step 3: Delete old certificate..."
gcloud compute ssl-certificates delete librechat-ssl-cert --global --quiet
echo ""

echo "Step 4: Rename new certificate to original name..."
# Can't rename in GCP, so we'll keep the new name
echo "New certificate name: librechat-ssl-cert-new"
echo ""

echo "Step 5: Check new certificate status..."
gcloud compute ssl-certificates describe librechat-ssl-cert-new --global
echo ""

echo "=========================================="
echo "SSL Certificate Recreated"
echo "=========================================="
echo ""
echo "Certificate will provision in 15-60 minutes now that DNS is correct."
echo ""
echo "Check status with:"
echo "  gcloud compute ssl-certificates describe librechat-ssl-cert-new --global"
echo ""
echo "Look for:"
echo "  status: ACTIVE"
echo "  domainStatus:"
echo "    chat.tersona.terpedia.com: ACTIVE"
echo ""
