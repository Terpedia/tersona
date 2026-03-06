# Podcast export: voice conversations and text-to-podcast

LibreChat at **chat.tersona.terpedia.com** does not ship with “save as podcast” out of the box. This document describes how to add:

1. **Voice conversation → podcast**: Save a voice chat as an episode (e.g. MP3 + RSS).
2. **Text conversation → podcast**: Convert a text thread into an episode using TTS; the **interviewer (TerpeneQueen)** is spoken with **Susan Trapp’s trained Google voice**.

## Overview

- **TerpeneQueen (Susan Trapp, PhD)** is the host. Her lines are always synthesized with **Google Cloud Text-to-Speech Custom Voice** (trained from Susan’s recordings).
- **Guest/user** lines can be:
  - **Voice conversations**: Real audio from the LibreChat voice session (recorded and uploaded to the export service).
  - **Text conversations**: Synthesized with a different TTS voice (e.g. Google standard or ElevenLabs).

The **podcast-export** service (in `podcast-export/`) implements:

- An API to submit a conversation (text or references to voice segments).
- Generation of a single MP3 per “episode” (intro optional, host lines via Susan’s voice, guest lines from recording or TTS).
- Optional RSS feed for a “Tersona / TerpeneQueen” podcast show.

## User flows

### A. Voice conversation → podcast

1. User has a **voice** conversation in LibreChat with TerpeneQueen (or another agent).
2. User (or the front end) records the session or exports it (if LibreChat adds export).
3. User hits “Save as podcast” and uploads:
   - The **audio file** of the conversation, and/or
   - A **transcript** (or turn-by-turn segments) so the service can split and tag “host” vs “guest.”
4. Export service:
   - Optionally adds a short intro/outro with TerpeneQueen TTS (Susan’s voice).
   - Produces one MP3 and, if needed, updates the podcast RSS.

### B. Text conversation → podcast

1. User has a **text** conversation in LibreChat (e.g. with TerpeneQueen).
2. User clicks “Convert to podcast” (or similar) in the UI.
3. Front end sends the **conversation payload** (messages with role + text) to the podcast-export API.
4. Export service:
   - Sends all **TerpeneQueen/host** messages to **Google Cloud TTS** with **Susan Trapp’s Custom Voice**.
   - Sends **user/guest** messages to TTS with a default voice (or configured second voice).
   - Concatenates audio in order, adds intro/outro if configured.
   - Returns MP3 (and optionally registers the episode in RSS).

## API sketch (podcast-export service)

- **POST /api/export/text**
  - Body: `{ conversationId?, messages: [ { role: "user"|"assistant", content: string } ] }`
  - Response: `{ episodeId, mp3Url, duration }` (and optionally RSS item).

- **POST /api/export/voice**
  - Body: multipart — audio file + optional transcript JSON for host/guest split.
  - Response: `{ episodeId, mp3Url, duration }`.

- **GET /api/feed**
  - Returns RSS XML for the Tersona/TerpeneQueen podcast (all exported episodes).

Authentication and authorization (e.g. only logged-in LibreChat users, or API key) should be added in implementation.

## Where it runs

- **Recommended**: Deploy the podcast-export service on **Cloud Run** (or same GCE VM as LibreChat) so it can call **Google Cloud TTS** with Susan’s custom voice and write MP3s to Cloud Storage; RSS can be generated on the fly or cached.
- **LibreChat**: No code change required; add a “Export as podcast” button in the UI that calls this service with the current conversation (and, for voice, the recorded audio if available).

## TerpeneQueen voice

- All host/TerpeneQueen lines use **Google Cloud Text-to-Speech** with the **Custom Voice** model trained for Susan Trapp.
- Training and deployment steps: **`GOOGLE_VOICE_SUSAN_TRAPP.md`**.

## Checklist

- [ ] Podcast-export service implemented and deployed (e.g. Cloud Run).
- [ ] Google Custom Voice for Susan Trapp deployed and used for host TTS.
- [ ] Text export flow: conversation → TTS (host + guest) → MP3 + optional RSS.
- [ ] Voice export flow: audio + optional transcript → MP3 + optional RSS.
- [ ] LibreChat UI: “Export as podcast” / “Convert to podcast” calling the export API.
