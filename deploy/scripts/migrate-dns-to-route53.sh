#!/usr/bin/env bash
# Migrate DNS from SiteGround to Route 53
# This script adds all existing DNS records to Route 53
# Run: ./deploy/scripts/migrate-dns-to-route53.sh

set -e

PROFILE="${AWS_PROFILE:-terpedia}"
ZONE_ID="Z1008515TFY6OXJW5Z47"
GCP_LB_IP="34.110.252.202"
SITEGROUND_IP="34.69.142.169"

echo "=========================================="
echo "DNS Migration: SiteGround → Route 53"
echo "=========================================="
echo "Profile: $PROFILE"
echo "Hosted Zone: $ZONE_ID (terpedia.com)"
echo ""

# 1. Main domain A record (terpedia.com → SiteGround)
echo "1. Adding A record: terpedia.com → $SITEGROUND_IP (SiteGround)"
aws route53 change-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "terpedia.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'"$SITEGROUND_IP"'"}]
      }
    }]
  }' --output text --query "ChangeInfo.Status"
echo ""

# 2. Google MX records (email)
echo "2. Adding MX records (Google Workspace email)"
aws route53 change-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "terpedia.com",
        "Type": "MX",
        "TTL": 300,
        "ResourceRecords": [
          {"Value": "1 aspmx.l.google.com"},
          {"Value": "5 alt1.aspmx.l.google.com"},
          {"Value": "5 alt2.aspmx.l.google.com"},
          {"Value": "10 alt3.aspmx.l.google.com"},
          {"Value": "10 alt4.aspmx.l.google.com"}
        ]
      }
    }]
  }' --output text --query "ChangeInfo.Status"
echo ""

# 3. Google site verification TXT record
echo "3. Adding TXT record (Google site verification)"
aws route53 change-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "terpedia.com",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [{"Value": "\"google-site-verification=-ysMDlO7g4ZAlo5fvn9L5XM9tQRUWlo_UWgeTIu3AZM\""}]
      }
    }]
  }' --output text --query "ChangeInfo.Status"
echo ""

# 4. Chat subdomain A record (already exists, but ensuring it's there)
echo "4. Adding A record: chat.tersona.terpedia.com → $GCP_LB_IP (GCP)"
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

# 5. Tersona CNAME (already exists, but ensuring it's there)
echo "5. Adding CNAME: tersona.terpedia.com → chat.tersona.terpedia.com"
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

echo "=========================================="
echo "✅ DNS Records Added to Route 53"
echo "=========================================="
echo ""
echo "Current records in Route 53:"
aws route53 list-resource-record-sets --profile "$PROFILE" --hosted-zone-id "$ZONE_ID" \
  --query "ResourceRecordSets[?Type!='NS' && Type!='SOA'].[Name,Type,ResourceRecords[0].Value]" \
  --output table
echo ""

echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo ""
echo "1. Update nameservers at your domain registrar to:"
echo "   ns-1847.awsdns-38.co.uk"
echo "   ns-1031.awsdns-00.org"
echo "   ns-50.awsdns-06.com"
echo "   ns-811.awsdns-37.net"
echo ""
echo "2. Wait 24-48 hours for DNS propagation"
echo ""
echo "3. Verify with: dig terpedia.com NS +short"
echo ""
echo "4. Once propagated, SSL cert will auto-provision for chat.tersona.terpedia.com"
echo ""
echo "⚠️  IMPORTANT: Don't delete SiteGround DNS until Route 53 is fully working!"
echo ""
