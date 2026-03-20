# Gemini API Proxy - Cloud Function

Cloud Function that proxies Gemini API calls, keeping the API key secure on the server side.

## Architecture

```
Browser (GitHub Pages)
├─→ Cloud Function (Gemini Proxy) → Gemini API (our API key)
└─→ Cloud Run (STT/TTS) → Google Cloud APIs (service account)
```

## Setup

1. **Get Gemini API Key:**
   - Go to https://aistudio.google.com/apikey
   - Create or copy your API key

2. **Deploy:**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ./deploy.sh
   ```

   Or set it as a secret in Google Cloud:
   ```bash
   echo -n "your-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
   ```

3. **Update Frontend:**
   - Use the Cloud Function URL for chat API calls
   - Use Cloud Run URL for STT/TTS calls

## Endpoints

- `POST /chat` - Proxies Gemini API calls
  - Body: `{ "message": str, "active_terpenes": List[str], "conversation_history": List[Dict] }`
  - Returns: `{ "responses": [{ "terpene_id": str, "response": str }], "conversation_history": List[Dict] }`

## Environment Variables

- `GEMINI_API_KEY` - Your Gemini API key (set as secret or env var)

## Security

- API key is never exposed to the browser
- CORS enabled for tersona.terpedia.com
- Unauthenticated access (can add auth if needed)
