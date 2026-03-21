# TerpeneQueen Chat — GitHub Pages

Simple chat interface for **TerpeneQueen (Susan Trapp, PhD)** using **Google Vertex AI**, **Speech-to-Text**, and **Text-to-Speech**, deployed to GitHub Pages at **tersona.terpedia.com**.

## Features

- 🫅🏼 **TerpeneQueen persona** — Expert interviewer on terpenes, cannabis botany, natural products
- 🌿 **Full panel** — All terpene personas are included by default (no picker)
- 💬 **Text chat** — Type messages and get text + audio responses
- 🎤 **Voice chat** — Record audio, get audio responses (STT → AI → TTS)
- 🔊 **Audio playback** — Hear TerpeneQueen's responses in synthesized voice
- 📱 **Responsive design** — Works on desktop and mobile
- 🚀 **Static site** — No backend required for frontend (backend is Cloud Run)

## Architecture

```
User Browser (GitHub Pages)
    ↓
Cloud Run API (GCP)
    ├─→ Vertex AI Gemini (Chat with TerpeneQueen)
    ├─→ Cloud Speech-to-Text (User audio → text)
    └─→ Cloud Text-to-Speech (AI response → audio)
```

## Quick Start

### 1. Deploy Backend API

```bash
cd api/vertex-chat
./deploy.sh
```

This deploys the Cloud Run service. Note the **service URL** (e.g., `https://terpenequeen-api-xxx.run.app`).

### 2. Configure Frontend

Edit `docs/index.html` and update the API URL, OR users can enter it in the UI on first load.

### 3. Deploy Frontend

```bash
git add docs/ api/
git commit -m "Deploy TerpeneQueen audio chat"
git push origin main
```

GitHub Actions will auto-deploy to Pages.

### 4. Set Custom Domain

In GitHub **Settings** → **Pages**, add custom domain: `tersona.terpedia.com`

Update DNS: **CNAME** `tersona.terpedia.com` → `your-username.github.io`

## Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** — GitHub Pages deployment guide
- **[AUDIO_CHAT_SETUP.md](./AUDIO_CHAT_SETUP.md)** — Complete audio chat setup
- **[../api/vertex-chat/README.md](../api/vertex-chat/README.md)** — Backend API documentation

## Usage

1. Visit `https://tersona.terpedia.com`
2. Enter your Cloud Run API URL (if not hardcoded)
3. Choose **Text** or **Voice** mode
4. Start chatting with TerpeneQueen!

### Text Mode
- Type your message
- Get text response + audio playback

### Voice Mode
- Click microphone button
- Speak your question
- Click again to stop
- Get audio response automatically

## API Key Security

⚠️ **Note**: The backend uses **service account authentication** (no user API keys needed). The Cloud Run service handles all Google Cloud API calls securely.

Users only need to provide the **Cloud Run service URL** (which can be public or require auth, depending on your setup).

## TerpeneQueen System Prompt

The persona is defined in the backend API (`api/vertex-chat/main.py`) and includes:
- Expert knowledge in terpenes, cannabis botany, natural products
- Warm, professional interviewer style
- First-person as Susan Trapp, PhD
- Conversational but informative tone

See `../deploy/librechat-gcp/docs/TERPENEQUEEN.md` for the full persona definition.

## Troubleshooting

See **[AUDIO_CHAT_SETUP.md](./AUDIO_CHAT_SETUP.md)** for detailed troubleshooting.

Common issues:
- **API URL not set** — Enter Cloud Run service URL in the UI
- **Microphone access** — Requires HTTPS (or localhost)
- **Service account permissions** — Check Cloud Run service account has required roles
- **CORS errors** — Ensure Cloud Run API allows your domain

## Development

- **Frontend**: `docs/index.html` (single HTML file)
- **Backend**: `api/vertex-chat/` (FastAPI on Cloud Run)
- **Deployment**: GitHub Actions (`.github/workflows/pages.yml`)

## Next Steps

- [ ] Train Susan Trapp's custom voice (see `../deploy/librechat-gcp/docs/GOOGLE_VOICE_SUSAN_TRAPP.md`)
- [ ] Set `CUSTOM_VOICE_NAME` in Cloud Run env vars
- [ ] Add podcast export feature
- [ ] Optimize audio quality and latency
