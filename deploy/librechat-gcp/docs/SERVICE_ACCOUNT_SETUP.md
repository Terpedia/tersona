# Google Cloud Service Account Setup

To enable Google Cloud Speech (STT/TTS) and Vertex AI for LibreChat, you need a service account with the proper permissions.

## Steps

### 1. Create Service Account

Go to [GCP Console → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts?project=terpedia-489015)

1. Click **Create Service Account**
2. Name: `librechat-speech` (or your choice)
3. Description: "Service account for LibreChat STT/TTS and Gemini"
4. Click **Create and Continue**

### 2. Grant Roles

Add these roles:
- **Vertex AI User** - For Gemini models
- **Cloud Speech Client** - For Speech-to-Text
- **Cloud Text-to-Speech Client** - For Text-to-Speech
- **Service Account Token Creator** (optional, for advanced features)

Click **Continue** then **Done**.

### 3. Create JSON Key

1. Find your new service account in the list
2. Click the three dots (⋮) → **Manage keys**
3. Click **Add Key** → **Create new key**
4. Choose **JSON**
5. Click **Create** - the key file downloads automatically

### 4. Save the Key

Save the downloaded JSON file as:
```
/Users/danielmcshan/GitHub/tersona/deploy/librechat-gcp/auth.json
```

**Important**: Do NOT commit `auth.json` to git. It's already in `.gitignore`.

### 5. Verify

The `auth.json` file should look like the `auth.json.example` file but with your actual credentials.

## Alternative: Use Generative Language API Only

If you don't want to set up a service account right now, you can continue using just the Generative Language API key (already configured in `.env` as `GOOGLE_KEY`). However, you won't have Google Cloud Speech (STT/TTS) until you set up the service account.

To disable the speech-bridge temporarily, comment it out in `docker-compose.yml` and switch back to OpenAI TTS/STT in `librechat.yaml`.
