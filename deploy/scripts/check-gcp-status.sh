#!/usr/bin/env bash
# Check GCP LibreChat deployment status
# Run: ./deploy/scripts/check-gcp-status.sh

set -e

PROJECT="terpedia-489015"

echo "=========================================="
echo "GCP LibreChat Status Check"
echo "=========================================="
echo "Project: $PROJECT"
echo ""

# Set project
gcloud config set project $PROJECT

echo "1. VM Instance Status:"
gcloud compute instances list --filter="name=librechat"
echo ""

echo "2. SSL Certificates:"
gcloud compute ssl-certificates list
echo ""

echo "3. Backend Services:"
gcloud compute backend-services list
echo ""

echo "4. Forwarding Rules (Load Balancer):"
gcloud compute forwarding-rules list
echo ""

echo "5. URL Maps:"
gcloud compute url-maps list
echo ""

echo "6. Target HTTPS Proxies:"
gcloud compute target-https-proxies list
echo ""

echo "7. Health Checks:"
gcloud compute health-checks list
echo ""

echo "=========================================="
echo "DNS Status:"
echo "=========================================="
dig chat.tersona.terpedia.com +short
echo ""

echo "=========================================="
echo "Testing Endpoints:"
echo "=========================================="
echo "HTTP (should redirect to HTTPS):"
curl -I http://chat.tersona.terpedia.com 2>&1 | head -5
echo ""

echo "HTTPS:"
curl -I https://chat.tersona.terpedia.com 2>&1 | head -10
echo ""

echo "Direct to Load Balancer IP:"
curl -I http://34.110.252.202 2>&1 | head -5
echo ""
