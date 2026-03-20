#!/usr/bin/env bash
# Route 53 DNS setup for tersona.terpedia.com (GitHub Pages) using profile terpedia.
# Run: ./scripts/route53-dns-setup.sh
# Requires: aws cli, profile terpedia configured.

set -e
PROFILE="${AWS_PROFILE:-terpedia}"
ZONE_ID="Z1008515TFY6OXJW5Z47"
GITHUB_PAGES_DOMAIN="Terpedia.github.io"  # Update if your GitHub Pages domain is different

echo "Using AWS profile: $PROFILE"
echo "Hosted zone: $ZONE_ID (terpedia.com)"
echo ""

# Delete A record: chat.tersona.terpedia.com (no longer needed)
echo "Deleting A record: chat.tersona.terpedia.com"
aws route53 change-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --change-batch '{
    "Changes": [{
      "Action": "DELETE",
      "ResourceRecordSet": {
        "Name": "chat.tersona.terpedia.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "34.110.252.202"}]
      }
    }]
  }' --output text --query "ChangeInfo.Status" 2>/dev/null || echo "Record not found or already deleted"
echo ""

# Ensure CNAME: tersona.terpedia.com -> GitHub Pages
echo "Setting CNAME: tersona.terpedia.com -> $GITHUB_PAGES_DOMAIN"
aws route53 change-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "tersona.terpedia.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'"$GITHUB_PAGES_DOMAIN"'"}]
      }
    }]
  }' --output text --query "ChangeInfo.Status"
echo ""

echo "Done. Nameservers for terpedia.com (set these at your registrar to use Route 53):"
aws route53 get-hosted-zone --profile "$PROFILE" --id "$ZONE_ID" \
  --query "DelegationSet.NameServers" --output text | tr '\t' '\n'
