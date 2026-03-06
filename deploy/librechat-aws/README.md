# LibreChat on AWS — chat.tersona.terpedia.com

Deploy LibreChat on AWS and serve it at **chat.tersona.terpedia.com**. Includes TerpeneQueen (Susan Trapp, PhD) as the interviewer persona and podcast export with Google Custom Voice.

## Architecture

- **EC2**: t3.xlarge instance running Docker Compose (LibreChat + MongoDB + Meilisearch + Speech-bridge)
- **ALB**: Application Load Balancer with HTTPS
- **ACM**: AWS-managed SSL certificate for chat.tersona.terpedia.com
- **Route53**: DNS (or configure at your registrar)
- **VPC**: Custom VPC with public subnets in 2 AZs

## Prerequisites

- AWS account (Account ID: 548217737835)
- AWS CLI configured with `terpedia` profile ✅
- Domain: chat.tersona.terpedia.com (or parent domain accessible for DNS)
- SSH key pair (will be created or specified)

## 1. Create SSH Key

```bash
cd /Users/danielmcshan/GitHub/tersona/deploy/librechat-aws

# Create SSH key pair
aws ec2 create-key-pair \
  --profile terpedia \
  --region us-east-1 \
  --key-name librechat-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/librechat-key.pem

chmod 400 ~/.ssh/librechat-key.pem
```

Or if you have an existing key, update `terraform.tfvars` with the key name.

## 2. Deploy Infrastructure (Terraform)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This creates:
- VPC and subnets
- EC2 instance with Docker
- Application Load Balancer
- Security groups
- ACM certificate (requires DNS validation)

## 3. Configure DNS

After Terraform completes, you'll get:
- ALB DNS name (e.g., `librechat-alb-123456789.us-east-1.elb.amazonaws.com`)
- Certificate validation DNS records

### Option A: Using Route53 (if terpedia.com is in Route53)
Terraform can create the records automatically (TODO: add Route53 config).

### Option B: External DNS (e.g., SiteGround)
1. Create CNAME record:
   - **Name**: `chat.tersona.terpedia.com`
   - **Value**: ALB DNS name from Terraform output
2. Create DNS validation record for ACM certificate:
   - Use the values from `certificate_validation_options` output

## 4. Deploy LibreChat

Copy files from `../librechat-gcp/` (they're the same):

```bash
cd /Users/danielmcshan/GitHub/tersona/deploy/librechat-aws

# Copy config files
cp ../librechat-gcp/.env .
cp ../librechat-gcp/auth.json .
cp ../librechat-gcp/docker-compose.yml .
cp ../librechat-gcp/docker-compose.override.yaml.example docker-compose.override.yaml
cp ../librechat-gcp/librechat.yaml .
cp -r ../librechat-gcp/speech-bridge .

# Update .env with AWS-appropriate values if needed
# DOMAIN_CLIENT should be chat.tersona.terpedia.com

# Deploy to EC2
./scripts/deploy-aws.sh
```

## 5. Access LibreChat

Once DNS propagates and certificate validates (15-60 minutes):
- https://chat.tersona.terpedia.com

## Files

| Path | Purpose |
|------|---------|
| `terraform/` | AWS infrastructure (VPC, EC2, ALB, ACM) |
| `.env` | Environment variables (copy from GCP deploy) |
| `docker-compose.yml` | LibreChat services (same as GCP) |
| `speech-bridge/` | Google Speech bridge (same as GCP) |
| `auth.json` | Google Cloud credentials (same as GCP) |
| `scripts/deploy-aws.sh` | Deploy script for AWS |

## Differences from GCP

- **Cloud Provider**: AWS instead of GCP
- **Load Balancer**: ALB instead of Google LB
- **SSL**: ACM certificate instead of Google-managed
- **Networking**: VPC/subnets instead of GCP default network
- **VM**: EC2 instead of GCE
- **Everything else**: Same (LibreChat, speech-bridge, Google Gemini, Google Speech)

## Costs (Estimate)

- EC2 t3.xlarge: ~$150/month
- ALB: ~$25/month + data transfer
- Data transfer: Variable
- **Total**: ~$175-200/month base

(GCP was similar: e2-standard-4 ~$130 + LB ~$20 + NAT ~$45 = ~$195/month)
