#!/usr/bin/env bash
# Update nameservers for terpedia.com (registered with AWS)
# This requires route53domains permissions
# Run: ./deploy/scripts/update-nameservers-aws.sh

set -e

PROFILE="${AWS_PROFILE:-terpedia}"
DOMAIN="terpedia.com"

echo "=========================================="
echo "Update Nameservers for $DOMAIN"
echo "=========================================="
echo "Profile: $PROFILE"
echo ""

# Get current nameservers
echo "Current nameservers:"
aws route53domains get-domain-detail --profile "$PROFILE" --domain-name "$DOMAIN" \
  --query "Nameservers[*].Name" --output table 2>&1 || {
  echo ""
  echo "⚠️  ERROR: No permission to access Route53 Domains"
  echo ""
  echo "You need to either:"
  echo "1. Add route53domains:* permissions to the IAM user"
  echo "2. Use AWS Console to update nameservers manually"
  echo ""
  echo "AWS Console URL:"
  echo "https://console.aws.amazon.com/route53/domains/home#/domains/terpedia.com"
  echo ""
  exit 1
}

echo ""
echo "Updating to Route 53 hosted zone nameservers..."
echo ""

# Update nameservers
aws route53domains update-domain-nameservers --profile "$PROFILE" --domain-name "$DOMAIN" \
  --nameservers \
    Name=ns-1847.awsdns-38.co.uk \
    Name=ns-1031.awsdns-00.org \
    Name=ns-50.awsdns-06.com \
    Name=ns-811.awsdns-37.net

echo ""
echo "✅ Nameservers updated!"
echo ""
echo "New nameservers:"
echo "  ns-1847.awsdns-38.co.uk"
echo "  ns-1031.awsdns-00.org"
echo "  ns-50.awsdns-06.com"
echo "  ns-811.awsdns-37.net"
echo ""
echo "Propagation will take 5-60 minutes."
echo ""
echo "Verify with: dig terpedia.com NS +short"
echo ""
