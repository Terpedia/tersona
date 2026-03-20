# Deployment Options

## Option 1: Minimal STT/TTS Backend (Recommended)

**Architecture:**
- **Gemini API**: Called directly from browser (user provides API key)
- **STT/TTS**: Minimal Cloud Run service (this repo)

**Pros:**
- Simpler architecture
- Lower cost (only STT/TTS backend)
- User manages their own Gemini API key
- No backend needed for chat

**Deploy:**
```bash
cd api/stt-tts-only
./deploy.sh
```

## Option 2: Full Backend with Vertex AI

**Architecture:**
- **Vertex AI**: Backend handles all chat (service account auth)
- **STT/TTS**: Same backend

**Pros:**
- Enterprise features
- Centralized authentication
- Better for production/teams

**Deploy:**
```bash
cd api/vertex-chat
./deploy.sh
```

## Recommendation

For your use case (GitHub Pages frontend), **Option 1** is better:
- Users can use their own Gemini API keys
- Simpler deployment
- Lower infrastructure cost
- Still get all terpene personalities and voices

The STT/TTS backend is minimal and only needed for voice features.
