#!/usr/bin/env bash
# Deploy LibreChat config to GCP VM and restart containers.
# Usage: ./scripts/deploy.sh [instance-name] [zone]
# Prerequisites: gcloud configured, terraform applied, and instance name/zone match terraform output.

set -e

INSTANCE="${1:-librechat}"
ZONE="${2:-us-central1-a}"
REMOTE_DIR="/opt/librechat"

echo "Deploying to $INSTANCE ($ZONE)..."

# Copy compose, config, and env example (do not overwrite .env if it exists)
gcloud compute scp --zone="$ZONE" \
  docker-compose.yml \
  docker-compose.override.yaml.example \
  librechat.yaml \
  .env.example \
  "$INSTANCE:$REMOTE_DIR/"

# Optional: copy override if you have one (uncomment and create docker-compose.override.yaml first)
# gcloud compute scp --zone="$ZONE" docker-compose.override.yaml "$INSTANCE:$REMOTE_DIR/"

gcloud compute ssh --zone="$ZONE" "$INSTANCE" --command="
  cd $REMOTE_DIR
  if [ ! -f .env ]; then cp .env.example .env; echo 'Created .env from example — edit with your API keys.'; fi
  if [ ! -f docker-compose.override.yaml ]; then cp docker-compose.override.yaml.example docker-compose.override.yaml; fi
  sudo docker compose pull
  sudo docker compose up -d
  echo 'LibreChat restarted.'
"

echo "Done. Open https://chat.tersona.terpedia.com (after DNS points to this VM/LB)."
