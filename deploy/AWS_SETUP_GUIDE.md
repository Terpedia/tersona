# Setting Up AWS Terpedia Profile

## Method 1: Interactive Setup (Recommended)

Run this command and follow the prompts:

```bash
aws configure --profile terpedia
```

You'll be asked for:
1. **AWS Access Key ID**: Your access key (starts with `AKIA...`)
2. **AWS Secret Access Key**: Your secret key
3. **Default region**: e.g., `us-east-1` or `us-west-2`
4. **Default output format**: `json` (recommended)

## Method 2: Manual Setup

### Edit credentials file:
```bash
nano ~/.aws/credentials
```

Add this section:
```ini
[terpedia]
aws_access_key_id = YOUR_ACCESS_KEY_HERE
aws_secret_access_key = YOUR_SECRET_KEY_HERE
```

### Edit config file:
```bash
nano ~/.aws/config
```

Add this section:
```ini
[profile terpedia]
region = us-east-1
output = json
```

## Method 3: AWS SSO (If using AWS Organizations)

```bash
aws configure sso --profile terpedia
```

Follow the prompts to authenticate via your browser.

## Getting AWS Credentials

If you don't have AWS credentials yet:

1. **Log into AWS Console**: https://console.aws.amazon.com
2. Go to **IAM** → **Users** → Your username
3. Click **Security credentials** tab
4. Click **Create access key**
5. Choose **CLI** as use case
6. Download or copy the Access Key ID and Secret Access Key

**Important**: Save the secret key immediately - you can't view it again!

## Verify Setup

After configuring, test it:

```bash
aws sts get-caller-identity --profile terpedia
```

Should return your AWS account ID and user info.

## For Terpedia.com Deployment

Once configured, we'll use this profile for:
- EC2 instances for LibreChat
- RDS for database (optional)
- ALB (Application Load Balancer)
- Route53 for DNS (if managing terpedia.com DNS)
- ACM for SSL certificates

---

**Which method would you like to use?** I can guide you through whichever you prefer.
