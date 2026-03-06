# Tersona

Voice-powered terpene personas for [Terpedia.com](https://terpedia.com). Talk to terpenes with STT/LLM/TTS — each tersona has properties, bioactivity, and a distinct voice.

## Projects

### 1. LibreChat on GCP — chat.tersona.terpedia.com ✅ DEPLOYED

Full-featured chat application with:
- **TerpeneQueen** (Susan Trapp, PhD) as interviewer persona
- **Google Gemini** AI (gemini-2.0-flash, 1.5-flash, 1.5-pro)
- **Google Cloud Speech** (STT/TTS via FastAPI bridge)
- **Podcast Export** capabilities (voice + text-to-podcast)
- **Custom Voice** infrastructure for Susan Trapp

**Status**: Running on GCP  
**URL**: https://chat.tersona.terpedia.com (after DNS propagates)  
**Docs**: [deploy/librechat-gcp/](deploy/librechat-gcp/)

### 2. Astro Front End — GitHub Pages (In Progress)

GitHub Pages site to chat with 10 terpene personas (see `src/`).

## Quick Links

- **GCP Deployment Guide**: [deploy/librechat-gcp/README.md](deploy/librechat-gcp/README.md)
- **Route 53 Setup**: [deploy/ROUTE53_SETUP_COMPLETE.md](deploy/ROUTE53_SETUP_COMPLETE.md)
- **TerpeneQueen Persona**: [deploy/librechat-gcp/docs/TERPENEQUEEN.md](deploy/librechat-gcp/docs/TERPENEQUEEN.md)
- **Podcast Export**: [deploy/librechat-gcp/docs/PODCAST_EXPORT.md](deploy/librechat-gcp/docs/PODCAST_EXPORT.md)
- **Train Susan's Voice**: [deploy/librechat-gcp/docs/GOOGLE_VOICE_SUSAN_TRAPP.md](deploy/librechat-gcp/docs/GOOGLE_VOICE_SUSAN_TRAPP.md)

## Infrastructure

### GCP Resources
- VM: librechat (e2-standard-4, us-central1-a)
- Load Balancer: 34.110.252.202
- Cloud NAT for outbound internet
- Google-managed SSL certificate

### AWS Resources
- Route 53 Hosted Zone: terpedia.com (Z1008515TFY6OXJW5Z47)
- DNS: chat.tersona.terpedia.com → GCP LB

### Services Running
- LibreChat API
- MongoDB (database)
- Meilisearch (conversation search)
- Speech-bridge (Google STT/TTS)

## Next Steps

1. **Complete DNS setup** - See [ROUTE53_SETUP_COMPLETE.md](deploy/ROUTE53_SETUP_COMPLETE.md)
2. **Wait for SSL** - Certificate auto-provisions after DNS
3. **Create TerpeneQueen** - Set up agent in LibreChat UI
4. **Record Susan's voice** - Train Google Custom Voice (optional)
