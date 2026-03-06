# Train a Google voice for Susan Trapp (TerpeneQueen)

This guide walks through training a **Google Cloud Text-to-Speech Custom Voice** from Susan Trapp’s recordings so that TerpeneQueen’s lines in chat and in **podcast export** are spoken in her voice.

## Why Google Custom Voice

- **LibreChat** supports TTS via OpenAI, Azure, ElevenLabs, and LocalAI. It does **not** natively support Google Cloud TTS or Custom Voice.
- For **podcast export** (see `PODCAST_EXPORT.md`), we use a separate service that calls **Google Cloud Text-to-Speech** with a **Custom Voice** model. That model is trained from Susan’s recordings.
- Once the custom voice is deployed, you can also use it in a small TTS proxy so LibreChat can play TerpeneQueen’s replies in Susan’s voice (optional).

## Prerequisites

- Google Cloud project with **billing** enabled.
- **Text-to-Speech API** enabled (and **Custom Voice** access; may require allowlist — see [Custom Voice](https://cloud.google.com/text-to-speech/custom-voice/docs)).
- Susan Trapp’s consent and rights to use her voice for this product.

## 1. Training data requirements (Google’s rules)

- **~500 utterances** (individual recordings).
- **~20–30 minutes** of total speech.
- **One WAV file per line** (e.g. `0001.wav`, `0002.wav`, …).
- **Consistent** energy, persona, and recording setup.
- **Script**: each line must match what was said (used for alignment).
- **Consent**: Google requires a **consent statement** from the voice talent (Susan) confirming use of her voice for synthetic speech.

Format:

- **Audio**: WAV, 16 kHz or 24 kHz, 16-bit PCM, mono (or as specified in [training data](https://cloud.google.com/text-to-speech/custom-voice/docs/training-data)).
- **Script**: CSV mapping file names to transcript text (e.g. `0001.wav, "Hello, welcome to the show."`).

## 2. Recording process

1. **Script**: Use Google’s suggested scripts or create your own (e.g. terpene-related phrases and general interview lines so the voice fits TerpeneQueen). Ensure enough variety and length to hit ~500 lines.
2. **Studio**: Quiet room, consistent mic and levels, same distance from mic.
3. **Recording**: One take per line; save as `0001.wav`, `0002.wav`, etc.
4. **CSV**: Create a CSV (e.g. `metadata.csv`) with columns like `filename,text` for every WAV.
5. **Consent**: Have Susan sign a consent form stating her voice may be used to create a synthetic voice for Terpedia/Tersona. Google will ask for this.

Optional: use the open-source **Voice Builder** ([GitHub](https://github.com/google/voice-builder)) to organize scripts and check alignment.

## 3. Upload and create the custom voice

1. **Cloud Storage bucket** (in the same project as TTS):
   ```bash
   gsutil mb -p YOUR_PROJECT -l us-central1 gs://YOUR_PROJECT-susan-voice-data
   ```
2. **Upload WAVs and CSV**:
   ```bash
   gsutil -m cp /path/to/wavs/*.wav gs://YOUR_PROJECT-susan-voice-data/
   gsutil cp metadata.csv gs://YOUR_PROJECT-susan-voice-data/
   ```
3. **Custom Voice UI**:
   - In Google Cloud Console go to **APIs & Services** → **Text-to-Speech** (or the [Custom Voice](https://console.cloud.google.com/text-to-speech/custom-voice) page).
   - Create a new **Custom Voice** model (e.g. “susan-trapp-terpenequeen”).
   - **Language**: Choose the primary language (e.g. English (US)).
   - **Training data**: Point to the bucket path (folder of WAVs + CSV).
   - **Consent**: Upload Susan’s signed consent statement.
   - Start training.

Training can take **up to a few days**. Google may then review the model (e.g. **2–3 weeks**) before it is available for use.

## 4. After deployment: using the voice

Once the custom voice is **deployed** and enabled for your project:

- **Voice name**: You’ll get a voice name (e.g. `custom-susan-trapp-terpenequeen` or similar) and possibly a **custom voice ID**.
- **API calls**: In your podcast-export service (and any TTS proxy), call the Text-to-Speech API with:
  - `voice.name` or the custom voice identifier, and
  - `languageCode` matching the model (e.g. `en-US`).

Example (conceptual) for podcast-export:

```json
{
  "input": { "text": "Welcome to Tersona. I'm Susan Trapp." },
  "voice": {
    "languageCode": "en-US",
    "name": "custom-susan-trapp-terpenequeen"
  },
  "audioConfig": { "audioEncoding": "MP3", "speakingRate": 1.0 }
}
```

Exact field names depend on the [Custom Voice API](https://cloud.google.com/text-to-speech/custom-voice/docs/using-api); use the “custom voice” variant of the TTS request.

## 5. IAM and security

- Restrict **Custom Voice** and **TTS** to the service account used by the podcast-export service (and TTS proxy, if any).
- Do not expose API keys or service account keys in the front end; keep TTS calls server-side only.

## Checklist

- [ ] Text-to-Speech API and Custom Voice access enabled (and allowlist if required).
- [ ] ~500 WAVs + CSV + consent from Susan.
- [ ] Data uploaded to GCS; Custom Voice model created and training started.
- [ ] Model approved and deployed; voice name/ID noted.
- [ ] Podcast-export service (and optional TTS proxy) updated to use Susan’s custom voice for TerpeneQueen.
- [ ] IAM limited to the service accounts that need TTS.

## References

- [Custom Voice user guide](https://cloud.google.com/text-to-speech/custom-voice/docs/user-guide)
- [Training data requirements](https://cloud.google.com/text-to-speech/custom-voice/docs/training-data)
- [Using your deployed custom voice](https://cloud.google.com/text-to-speech/custom-voice/docs/quickstart)
- [Voice Builder (GitHub)](https://github.com/google/voice-builder)
