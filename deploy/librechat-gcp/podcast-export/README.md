# Podcast export service

Converts LibreChat conversations into podcast episodes:

- **Text → podcast**: Conversation messages are sent to Google Cloud Text-to-Speech; **TerpeneQueen (Susan Trapp)** host lines use her **Custom Voice**; guest/user lines use a default voice. Output: MP3 + optional RSS.
- **Voice → podcast**: Upload recorded voice conversation audio (+ optional transcript for host/guest split). Service adds intro/outro with TerpeneQueen TTS and produces MP3 + RSS.

## Prerequisites

- Google Cloud project with **Text-to-Speech API** enabled and **Custom Voice** deployed for Susan Trapp (see `../docs/GOOGLE_VOICE_SUSAN_TRAPP.md`).
- **Cloud Storage** bucket for generated MP3s (optional; can stream response instead).

## Design

- **API** (e.g. Cloud Run or same VM as LibreChat):
  - `POST /api/export/text` — body: `{ conversationId?, messages: [ { role, content } ] }` → returns `{ episodeId, mp3Url }`.
  - `POST /api/export/voice` — multipart: audio file + optional transcript JSON → returns `{ episodeId, mp3Url }`.
  - `GET /api/feed` — returns RSS for the Tersona/TerpeneQueen show.
- **TTS**: Host role → Google Cloud TTS with Susan’s custom voice; user/guest → default TTS voice.
- **Auth**: Add API key or validate LibreChat JWT so only authorized users can export.

## Implementation status

- [ ] Implement text-to-podcast (fetch messages → TTS → concatenate → MP3).
- [ ] Implement voice-to-podcast (upload audio + optional transcript → segment + TTS intro/outro → MP3).
- [ ] RSS feed generation and storage of episode metadata.
- [ ] Deploy to Cloud Run (or VM); configure env (GCP project, bucket, custom voice name).
- [ ] LibreChat UI: “Export as podcast” / “Convert to podcast” button calling this API.

See `../docs/PODCAST_EXPORT.md` for full design.
