#!/usr/bin/env bash
# Route 53 DNS setup for chat.tersona.terpedia.com using profile terpedia.
# Run: ./scripts/route53-dns-setup.sh
# Requires: aws cli, profile terpedia configured.

set -e
PROFILE="${AWS_PROFILE:-terpedia}"
ZONE_ID="Z1008515TFY6OXJW5Z47"
GCP_LB_IP="34.110.252.202"

echo "Using AWS profile: $PROFILE"
echo "Hosted zone: $ZONE_ID (terpedia.com)"
echo ""

# Ensure A record: chat.tersona.terpedia.com -> GCP LB
echo "Setting A record: chat.tersona.terpedia.com -> $GCP_LB_IP"
aws route53 change-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "chat.tersona.terpedia.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'"$GCP_LB_IP"'"}]
      }
    }]
  }' --output text --query "ChangeInfo.Status"
echo ""

# Ensure CNAME: tersona.terpedia.com -> chat.tersona.terpedia.com
echo "Setting CNAME: tersona.terpedia.com -> chat.tersona.terpedia.com"
aws route53 change-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "tersona.terpedia.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "chat.tersona.terpedia.com"}]
      }
    }]
  }' --output text --query "ChangeInfo.Status"
echo ""

echo "Done. Nameservers for terpedia.com (set these at your registrar to use Route 53):"
aws route53 get-hosted-zone --profile "$PROFILE" --id "$ZONE_ID" \
  --query "DelegationSet.NameServers" --output text | tr '\t' '\n'
