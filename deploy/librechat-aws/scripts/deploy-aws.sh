#!/usr/bin/env bash
# Deploy LibreChat to AWS EC2 instance
# Usage: ./deploy-aws.sh [instance-id]

set -e

INSTANCE_ID="${1:-}"
REGION="us-east-1"

if [ -z "$INSTANCE_ID" ]; then
  echo "Finding instance..."
  INSTANCE_ID=$(aws ec2 describe-instances \
    --profile terpedia \
    --region $REGION \
    --filters "Name=tag:Name,Values=librechat" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)
fi

if [ "$INSTANCE_ID" = "None" ] || [ -z "$INSTANCE_ID" ]; then
  echo "Error: No running instance found. Run terraform apply first."
  exit 1
fi

echo "Deploying to instance: $INSTANCE_ID"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --profile terpedia \
  --region $REGION \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Instance IP: $PUBLIC_IP"

# Copy files
echo "Copying files..."
scp -i ~/.ssh/librechat-key.pem \
  docker-compose.yml \
  docker-compose.override.yaml \
  librechat.yaml \
  .env \
  auth.json \
  ubuntu@$PUBLIC_IP:~/

scp -i ~/.ssh/librechat-key.pem -r speech-bridge ubuntu@$PUBLIC_IP:~/

# Deploy on instance
echo "Setting up LibreChat..."
ssh -i ~/.ssh/librechat-key.pem ubuntu@$PUBLIC_IP << 'ENDSSH'
sudo mv ~/docker-compose.yml ~/docker-compose.override.yaml ~/librechat.yaml ~/.env ~/auth.json ~/speech-bridge /opt/librechat/
cd /opt/librechat
mkdir -p data-node meili_data images uploads logs
echo "UID=0" >> .env
echo "GID=0" >> .env
sudo docker compose pull
sudo docker compose up -d
sleep 5
sudo docker compose ps
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo "Access at: https://chat.tersona.terpedia.com (after DNS propagates)"
