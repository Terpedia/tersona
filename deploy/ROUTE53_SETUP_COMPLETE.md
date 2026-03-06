# Route 53 DNS Configuration — COMPLETE

## ✅ Hosted Zone Created

**Domain**: terpedia.com  
**Hosted Zone ID**: Z1008515TFY6OXJW5Z47  
**Status**: Active

### Name Servers (Update at your registrar)
You need to update the nameservers at your domain registrar (e.g., GoDaddy, Namecheap) to:

```
ns-1847.awsdns-38.co.uk
ns-1031.awsdns-00.org
ns-50.awsdns-06.com
ns-811.awsdns-37.net
```

## ✅ DNS Records Created

| Record | Type | Value | Purpose |
|--------|------|-------|---------|
| chat.tersona.terpedia.com | A | 34.110.252.202 | Points to GCP Load Balancer |
| tersona.terpedia.com | CNAME | chat.tersona.terpedia.com | Alias to chat subdomain |

## 🌐 How to Complete DNS Setup

### If terpedia.com is currently on SiteGround:

You have **two options**:

#### Option 1: Keep DNS on SiteGround (Easier)
Don't update nameservers. Instead, manually add these DNS records in SiteGround:

1. Log into SiteGround → Domain → DNS Zone Editor
2. Add A record:
   - **Name**: `chat.tersona.terpedia.com`
   - **Type**: A
   - **Value**: `34.110.252.202`
3. Add CNAME record:
   - **Name**: `tersona.terpedia.com`
   - **Type**: CNAME
   - **Value**: `chat.tersona.terpedia.com`

Then **delete the Route 53 hosted zone** (to avoid confusion and AWS charges):
```bash
aws route53 delete-hosted-zone --profile terpedia --id Z1008515TFY6OXJW5Z47
```

#### Option 2: Move DNS to Route 53 (Full migration)
1. Update nameservers at your registrar to the Route 53 nameservers listed above
2. Wait 24-48 hours for propagation
3. Migrate all existing DNS records from SiteGround to Route 53

**Recommendation**: Use **Option 1** if terpedia.com is already working on SiteGround. Less disruption.

## ✅ LibreChat Status

**Services Running on GCP:**
- ✅ LibreChat API (port 3080)
- ✅ MongoDB (database)
- ✅ Meilisearch (search)
- ✅ Speech-bridge (Google STT/TTS)

**GCP Load Balancer IP**: 34.110.252.202  
**SSL Certificate**: Google-managed (will provision after DNS)

## 🔗 Access URLs

Once DNS propagates (5-60 minutes):
- **Main**: https://chat.tersona.terpedia.com
- **Alias**: https://tersona.terpedia.com (redirects to chat)

## ⚠️ Important Next Steps

1. **Update DNS**: Choose Option 1 (SiteGround) or Option 2 (Route 53 migration) above
2. **Wait for SSL**: Google-managed certificate will auto-provision after DNS resolves
3. **Test**: Visit https://chat.tersona.terpedia.com
4. **Create TerpeneQueen**: Set up the agent in LibreChat UI

## 📊 Current Status

- ✅ Route 53 hosted zone created
- ✅ DNS records created in Route 53
- ✅ LibreChat running on GCP
- ✅ All services healthy
- ⏳ DNS propagation (waiting for your choice on Option 1 or 2)
- ⏳ SSL certificate (after DNS)

## Management

**Profile**: Use `--profile terpedia` for all Route 53 commands.

View/edit DNS records:
```bash
# List all records
aws route53 list-resource-record-sets \
  --profile terpedia \
  --hosted-zone-id Z1008515TFY6OXJW5Z47

# Re-apply A + CNAME (from repo)
./scripts/route53-dns-setup.sh
```

Or use AWS Console:  
https://console.aws.amazon.com/route53/v2/hostedzones#ListRecordSets/Z1008515TFY6OXJW5Z47
