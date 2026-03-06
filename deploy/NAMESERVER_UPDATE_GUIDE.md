# Update Nameservers to Route 53

## ✅ DNS Records Migrated

All existing DNS records from SiteGround have been copied to Route 53:
- ✅ terpedia.com → 34.69.142.169 (SiteGround hosting)
- ✅ Google Workspace MX records (email)
- ✅ Google site verification TXT record
- ✅ chat.tersona.terpedia.com → 34.110.252.202 (GCP LibreChat)
- ✅ tersona.terpedia.com → chat.tersona.terpedia.com (CNAME)

## Next Step: Update Nameservers at Registrar

You need to update the nameservers at your domain registrar (where you purchased terpedia.com).

### Route 53 Nameservers (use these):
```
ns-1847.awsdns-38.co.uk
ns-1031.awsdns-00.org
ns-50.awsdns-06.com
ns-811.awsdns-37.net
```

### Current (incorrect) nameservers at registrar:
```
NS-1124.AWSDNS-12.ORG
NS-1971.AWSDNS-54.CO.UK
NS-376.AWSDNS-47.COM
NS-516.AWSDNS-00.NET
```

## How to Update Nameservers

### Domain is registered with AWS Route 53 (EASIEST)

Since terpedia.com is registered with AWS, update via AWS Console:

1. Go to: https://console.aws.amazon.com/route53/domains/home#/domains/terpedia.com
2. Click **Add or edit name servers**
3. Replace the current nameservers with:
   ```
   ns-1847.awsdns-38.co.uk
   ns-1031.awsdns-00.org
   ns-50.awsdns-06.com
   ns-811.awsdns-37.net
   ```
4. Click **Update**
5. Wait 5-60 minutes for propagation

### If registered with GoDaddy:
1. Log into GoDaddy account
2. Go to **My Products** → **Domains**
3. Click **DNS** next to terpedia.com
4. Scroll to **Nameservers** section
5. Click **Change**
6. Select **Custom** nameservers
7. Enter the 4 Route 53 nameservers above
8. Save

### If registered with Namecheap:
1. Log into Namecheap account
2. Go to **Domain List**
3. Click **Manage** next to terpedia.com
4. Find **Nameservers** section
5. Select **Custom DNS**
6. Enter the 4 Route 53 nameservers above
7. Save

### If registered with another registrar:
Look for "Nameservers", "DNS Settings", or "Name Server Management" in your registrar's control panel.

## Timeline

- **Immediate**: Nameserver update submitted
- **5-15 minutes**: Some DNS resolvers start using Route 53
- **24-48 hours**: Full global propagation
- **After propagation**: Google SSL cert auto-provisions for chat.tersona.terpedia.com

## Verification

Check if nameservers have propagated:
```bash
dig terpedia.com NS +short
```

Should return:
```
ns-1847.awsdns-38.co.uk.
ns-1031.awsdns-00.org.
ns-50.awsdns-06.com.
ns-811.awsdns-37.net.
```

Check if chat subdomain resolves:
```bash
dig chat.tersona.terpedia.com +short
```

Should return:
```
34.110.252.202
```

## After Propagation

1. Wait for Google SSL certificate to provision (15-60 minutes after DNS)
2. Check SSL status:
   ```bash
   gcloud compute ssl-certificates describe librechat-ssl-cert --global --project=terpedia-489015
   ```
3. Visit https://chat.tersona.terpedia.com
4. Create TerpeneQueen agent in LibreChat

## Important Notes

- ⚠️ Don't delete SiteGround DNS records until Route 53 is fully working
- ⚠️ Email (Google Workspace) will continue working - MX records are migrated
- ⚠️ Main site (terpedia.com) will continue working - A record points to SiteGround
- ✅ You can now manage all DNS in Route 53 AWS Console

## Route 53 Management

View/edit records:
```bash
# List all records
aws route53 list-resource-record-sets --profile terpedia --hosted-zone-id Z1008515TFY6OXJW5Z47

# AWS Console
https://console.aws.amazon.com/route53/v2/hostedzones#ListRecordSets/Z1008515TFY6OXJW5Z47
```

## Cost

Route 53 hosted zone: $0.50/month + $0.40 per million queries (very cheap for most sites)
