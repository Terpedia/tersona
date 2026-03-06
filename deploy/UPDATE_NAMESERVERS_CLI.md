# Update Nameservers via AWS CLI

## Problem
The `terpedia` IAM user doesn't have `route53domains:*` permissions needed to update nameservers via CLI.

## Solution Options

### Option 1: Use AWS Console (EASIEST - 2 minutes)

1. Go to: https://console.aws.amazon.com/route53/domains/home#/domains/terpedia.com
2. Click **Add or edit name servers**
3. Replace with these nameservers:
   ```
   ns-1847.awsdns-38.co.uk
   ns-1031.awsdns-00.org
   ns-50.awsdns-06.com
   ns-811.awsdns-37.net
   ```
4. Click **Update**
5. Wait 5-60 minutes for propagation

### Option 2: Add IAM Permissions (for CLI access)

If you have admin access to the AWS account, add Route53 Domains permissions:

#### Step 1: Create the policy
```bash
aws iam put-user-policy \
  --user-name terpedia \
  --policy-name Route53DomainsAccess \
  --policy-document file://deploy/aws-iam-policy-domains.json
```

#### Step 2: Update nameservers via CLI
```bash
aws route53domains update-domain-nameservers \
  --profile terpedia \
  --domain-name terpedia.com \
  --nameservers \
    Name=ns-1847.awsdns-38.co.uk \
    Name=ns-1031.awsdns-00.org \
    Name=ns-50.awsdns-06.com \
    Name=ns-811.awsdns-37.net
```

#### Step 3: Verify
```bash
aws route53domains get-domain-detail \
  --profile terpedia \
  --domain-name terpedia.com \
  --query "Nameservers[*].Name" \
  --output table
```

### Option 3: Use Different AWS Profile

If you have another AWS profile with admin access:

```bash
# List profiles
aws configure list-profiles

# Use admin profile
aws route53domains update-domain-nameservers \
  --profile <admin-profile-name> \
  --domain-name terpedia.com \
  --nameservers \
    Name=ns-1847.awsdns-38.co.uk \
    Name=ns-1031.awsdns-00.org \
    Name=ns-50.awsdns-06.com \
    Name=ns-811.awsdns-37.net
```

## Current Status

✅ DNS records migrated to Route 53:
- terpedia.com → 34.69.142.169 (SiteGround)
- Google Workspace MX records
- chat.tersona.terpedia.com → 34.110.252.202 (GCP)
- tersona.terpedia.com → chat.tersona.terpedia.com

⏳ Nameservers need to be updated (choose option above)

## After Nameserver Update

1. Verify DNS propagation (5-60 minutes):
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

2. Verify chat subdomain:
   ```bash
   dig chat.tersona.terpedia.com +short
   ```
   
   Should return:
   ```
   34.110.252.202
   ```

3. Wait for SSL certificate (15-60 minutes after DNS)

4. Visit https://chat.tersona.terpedia.com

## IAM Policy File

The required permissions are in: `deploy/aws-iam-policy-domains.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Route53DomainsPermissions",
      "Effect": "Allow",
      "Action": [
        "route53domains:GetDomainDetail",
        "route53domains:UpdateDomainNameservers",
        "route53domains:ListDomains",
        "route53domains:GetOperationDetail"
      ],
      "Resource": "*"
    }
  ]
}
```

## Recommendation

Use **Option 1** (AWS Console) - it's the fastest and doesn't require IAM permission changes.
