# Alternative: Use API Key Authentication (No Service Account Needed)

Since service account key creation is blocked, you can use **API key authentication** for Google Cloud Speech services instead.

## What you have already:
- ✅ Google Generative Language API key: `AQ.Ab8RN6IlLjDVB2WhYJBPzwcC3FpR8KVsoRh49A2oPNBLvaFgvA`
- ✅ This works for Gemini models in LibreChat

## For Google Cloud Speech (STT/TTS):

You need a **separate API key** for Cloud Speech services:

### 1. Enable the APIs:
```bash
gcloud services enable speech.googleapis.com --project=terpedia-489015
gcloud services enable texttospeech.googleapis.com --project=terpedia-489015
```

### 2. Create an API key:
```bash
gcloud alpha services api-keys create \
  --display-name="LibreChat Speech" \
  --project=terpedia-489015 \
  --api-target=service=speech.googleapis.com \
  --api-target=service=texttospeech.googleapis.com
```

### 3. Get the key value:
```bash
# List keys to find the one we just created
gcloud alpha services api-keys list --project=terpedia-489015

# Get the key string (use the ID from above)
gcloud alpha services api-keys get-key-string KEY_ID --project=terpedia-489015
```

### 4. Update the speech-bridge to use API key:

We'll modify `speech-bridge/main.py` to accept an API key instead of requiring service account credentials.

## Why this works:
- API keys can be used for Google Cloud Speech APIs
- No service account key creation needed
- Simpler authentication model
- Works around the organization policy

Let me know if you want me to implement this alternative approach!
