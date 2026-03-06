# AWS IAM Policy Setup for Terpedia LibreChat Deployment

## Option 1: Apply Policy via AWS Console (Easiest)

1. Go to https://console.aws.amazon.com/iam/
2. Click **Users** → Select your user (or create new user)
3. Click **Add permissions** → **Attach policies directly**
4. Click **Create policy**
5. Click **JSON** tab
6. Copy and paste the contents of `aws-iam-policy.json`
7. Click **Next**, name it `TerpediaLibreChatDeployment`
8. Click **Create policy**
9. Go back to your user and attach the newly created policy

## Option 2: Apply Policy via AWS CLI

```bash
# Create the policy
aws iam create-policy \
  --profile terpedia \
  --policy-name TerpediaLibreChatDeployment \
  --policy-document file://deploy/aws-iam-policy.json \
  --description "Permissions for deploying LibreChat infrastructure"

# Get your username
aws sts get-caller-identity --profile terpedia

# Attach to your user (replace YOUR_USERNAME and YOUR_ACCOUNT_ID)
aws iam attach-user-policy \
  --profile terpedia \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/TerpediaLibreChatDeployment
```

## Option 3: Use AWS Managed Policies (Quick but more permissive)

If you want to get started quickly without creating custom policies:

```bash
# Attach AWS managed policies (more permissive)
aws iam attach-user-policy \
  --profile terpedia \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws iam attach-user-policy \
  --profile terpedia \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess

aws iam attach-user-policy \
  --profile terpedia \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonRoute53FullAccess

aws iam attach-user-policy \
  --profile terpedia \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::aws:policy/AWSCertificateManagerFullAccess
```

## What This Policy Allows

The custom policy provides permissions for:

- ✅ **EC2**: Create/manage VPC, subnets, security groups, instances
- ✅ **ELB**: Create/manage Application Load Balancer
- ✅ **ACM**: Request and manage SSL certificates
- ✅ **Route53**: Manage DNS records for terpedia.com
- ✅ **IAM**: Create roles for EC2 instances
- ✅ **S3**: Store backups and static assets
- ✅ **RDS**: Optional managed MongoDB alternative (DocumentDB)
- ✅ **CloudWatch**: Monitoring and logs
- ✅ **Secrets Manager**: Store API keys securely
- ✅ **SSM**: Parameter store for configuration

## Verify Permissions

After attaching the policy:

```bash
# Verify your identity
aws sts get-caller-identity --profile terpedia

# Test EC2 permissions
aws ec2 describe-regions --profile terpedia

# Test Route53 permissions (if managing DNS)
aws route53 list-hosted-zones --profile terpedia
```

## Security Best Practices

1. **Use least privilege**: The custom policy is scoped to deployment needs
2. **Enable MFA**: Add multi-factor auth to your AWS account
3. **Rotate keys**: Rotate access keys every 90 days
4. **Use IAM roles**: Consider using IAM roles instead of access keys when possible

## Next Steps

Once the policy is attached and verified:

```bash
# Verify it works
aws sts get-caller-identity --profile terpedia
```

Then I'll create the Terraform configuration to deploy LibreChat to AWS!
