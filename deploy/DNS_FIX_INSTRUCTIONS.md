# DNS Fix for chat.tersona.terpedia.com

## Problem
- Domain registrar has old/incorrect AWS nameservers
- DNS currently resolving to SiteGround (ns1/ns2.giow1015.siteground.us)
- Route53 records exist but aren't being used
- Site is unreachable at https://chat.tersona.terpedia.com

## Solution Options

### Option 1: Add Records to SiteGround (FASTEST - 5 minutes)

1. Log into SiteGround control panel
2. Go to: **Websites** → **terpedia.com** → **Site Tools** → **Domain** → **DNS Zone Editor**
3. Add these two records:

**Record 1 - A Record:**
- Name/Host: `chat.tersona`
- Type: `A`
- Points to: `34.110.252.202`
- TTL: `14400` (or default)

**Record 2 - CNAME Record:**
- Name/Host: `tersona`
- Type: `CNAME`
- Points to: `chat.tersona.terpedia.com`
- TTL: `14400` (or default)

4. Save and wait 5-15 minutes for propagation
5. Test: `dig chat.tersona.terpedia.com +short` should return `34.110.252.202`

### Option 2: Fix Route53 Nameservers (COMPLETE - 24-48 hours)

Update nameservers at your domain registrar to:
```
ns-1847.awsdns-38.co.uk
ns-1031.awsdns-00.org
ns-50.awsdns-06.com
ns-811.awsdns-37.net
```

**Current (wrong) nameservers at registrar:**
```
NS-1124.AWSDNS-12.ORG
NS-1971.AWSDNS-54.CO.UK
NS-376.AWSDNS-47.COM
NS-516.AWSDNS-00.NET
```

These are from an old/different Route53 hosted zone.

## Recommendation

Use **Option 1** (SiteGround) because:
- Works in 5-15 minutes vs 24-48 hours
- No risk of breaking existing terpedia.com site
- Route53 records are already configured correctly
- You can migrate to full Route53 later if needed

## After DNS Works

Once `dig chat.tersona.terpedia.com` returns `34.110.252.202`:

1. Wait 15-60 minutes for Google SSL certificate to provision
2. Check SSL status:
   ```bash
   gcloud compute ssl-certificates describe librechat-ssl-cert --global --project=terpedia-489015
   ```
3. Visit https://chat.tersona.terpedia.com
4. Create TerpeneQueen agent in LibreChat UI

## Verification Commands

```bash
# Check DNS resolution
dig chat.tersona.terpedia.com +short

# Check current nameservers
dig terpedia.com NS +short

# Test HTTPS (after SSL provisions)
curl -I https://chat.tersona.terpedia.com
```
