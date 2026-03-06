# AWS IAM Policy Setup - Simplified

## Problem: Inline Policy Size Limit

AWS inline policies have a 2KB limit. The full policy exceeds this.

## Solution 1: Use AWS Managed Policies (EASIEST)

Attach these pre-existing AWS managed policies to your user:

```bash
# Get your username first
aws sts get-caller-identity --profile terpedia --query 'Arn' --output text

# Or if not configured yet, use default profile
USER_NAME="your-username-here"

# Attach managed policies
aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonRoute53FullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AWSCertificateManagerFullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
```

### Via AWS Console:
1. IAM → Users → Your user
2. Add permissions → Attach policies directly
3. Search and check:
   - `AmazonEC2FullAccess`
   - `ElasticLoadBalancingFullAccess`
   - `AmazonRoute53FullAccess`
   - `AWSCertificateManagerFullAccess`
   - `IAMFullAccess` (or IAMReadOnlyAccess if you want less)
4. Add permissions

## Solution 2: Create Customer Managed Policy (Better Security)

Customer managed policies have higher limits (6KB). Create via CLI:

```bash
cd /Users/danielmcshan/GitHub/tersona

# Create as customer managed policy (NOT inline)
aws iam create-policy \
  --policy-name TerpediaLibreChatDeploy \
  --policy-document file://deploy/aws-iam-policy.json \
  --description "LibreChat deployment permissions"

# Note the policy ARN from output, then attach it
aws iam attach-user-policy \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/TerpediaLibreChatDeploy
```

### Via AWS Console:
1. IAM → Policies → Create policy
2. JSON tab → Paste contents of `aws-iam-policy.json`
3. Next → Name: `TerpediaLibreChatDeploy`
4. Create policy
5. Go to Users → Your user → Add permissions
6. Attach the new policy

## Solution 3: Use Compact Policy (Less Secure)

I've created `aws-iam-policy-compact.json` (500 chars) that fits in inline policies.

**Warning**: Uses wildcards (*) which is less secure but more convenient.

```bash
# As inline policy
aws iam put-user-policy \
  --user-name YOUR_USERNAME \
  --policy-name TerpediaLibreChat \
  --policy-document file://deploy/aws-iam-policy-compact.json
```

## Recommendation

**Use Solution 1** (AWS Managed Policies) for quickest setup, or **Solution 2** (Customer Managed Policy) for better security with custom scope.

Both avoid the inline policy limit.

## Verify It Works

```bash
aws sts get-caller-identity --profile terpedia
aws ec2 describe-regions --profile terpedia --region us-east-1
```

If these work, you're ready to deploy!
