# Deployment Troubleshooting

## Permission Denied Errors

If you get `PERMISSION_DENIED` when deploying, try these solutions:

### Option 1: Use Local Docker Build (Recommended)

Build and push the image locally instead of using Cloud Build:

```bash
cd api/stt-tts-only
./deploy-local.sh
```

This avoids Cloud Build permissions entirely.

### Option 2: Request Permissions

Ask your GCP project admin to grant you:
- `Cloud Build Editor` role
- Or `Service Usage Admin` role

```bash
# Admin runs this:
gcloud projects add-iam-policy-binding terpedia-489015 \
  --member="user:dan@terpedia.com" \
  --role="roles/cloudbuild.builds.editor"
```

### Option 3: Use Service Account

Create a service account with deployment permissions:

```bash
# Create service account
gcloud iam service-accounts create deployer \
  --display-name="Deployment Service Account" \
  --project=terpedia-489015

# Grant permissions
gcloud projects add-iam-policy-binding terpedia-489015 \
  --member="serviceAccount:deployer@terpedia-489015.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding terpedia-489015 \
  --member="serviceAccount:deployer@terpedia-489015.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Use service account
gcloud auth activate-service-account deployer@terpedia-489015.iam.gserviceaccount.com \
  --key-file=path/to/key.json
```

### Option 4: Enable Required APIs

Make sure these APIs are enabled:

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  --project=terpedia-489015
```

## Common Issues

### "Artifact Registry API not enabled"
```bash
gcloud services enable artifactregistry.googleapis.com --project=terpedia-489015
```

### "Cloud Build bucket not found"
The project needs Cloud Build enabled. Use `deploy-local.sh` instead.

### "Service account lacks permissions"
The Cloud Run service needs a service account with:
- Cloud Speech Client
- Cloud Text-to-Speech Client

Set during deployment or via IAM.
