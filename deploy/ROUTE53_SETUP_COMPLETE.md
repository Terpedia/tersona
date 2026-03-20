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
| ~~chat.tersona.terpedia.com~~ | ~~A~~ | ~~34.110.252.202~~ | ~~Points to GCP Load Balancer~~ (REMOVED - no longer using LibreChat on GCP) |
| tersona.terpedia.com | CNAME | Terpedia.github.io | Points to GitHub Pages |

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

## ✅ Current Architecture

**Frontend (GitHub Pages):**
- ✅ Static site at `tersona.terpedia.com`
- ✅ Multi-terpene panel chat interface
- ✅ Text and voice chat modes

**Backend (Cloud Run):**
- Deploy separately using `api/vertex-chat/deploy.sh`
- Provides Vertex AI chat, STT, and TTS endpoints
- See `api/vertex-chat/README.md` for deployment

## 🔗 Access URLs

Once DNS propagates (5-60 minutes):
- **Main**: https://tersona.terpedia.com (GitHub Pages)
- **Backend API**: Deploy separately to Cloud Run (see `api/vertex-chat/README.md`)

## ⚠️ Important Next Steps

1. **DNS Updated**: `tersona.terpedia.com` now points to GitHub Pages
2. **Wait for DNS propagation**: 5-60 minutes (sometimes up to 24 hours)
3. **Wait for SSL**: GitHub Pages SSL will auto-provision after DNS resolves
4. **Deploy Backend**: Run `api/vertex-chat/deploy.sh` to deploy the Cloud Run API
5. **Test**: Visit https://tersona.terpedia.com and enter your Cloud Run API URL

## 📊 Current Status

- ✅ Route 53 hosted zone created
- ✅ DNS records updated: `tersona.terpedia.com` → GitHub Pages
- ✅ `chat.tersona.terpedia.com` A record removed (no longer needed)
- ✅ Frontend deployed to GitHub Pages
- ⏳ DNS propagation (5-60 minutes)
- ⏳ GitHub Pages SSL certificate (auto-provisions after DNS)
- ⏳ Backend API deployment (run `api/vertex-chat/deploy.sh`)

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
