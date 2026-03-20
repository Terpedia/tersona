"""
Minimal Cloud Run service for STT and TTS only
Gemini API is called directly from the browser
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from google.cloud import speech_v1, texttospeech_v1
import os
from typing import Optional

app = FastAPI(title="STT/TTS Service")

# CORS - allow GitHub Pages domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tersona.terpedia.com",
        "https://*.github.io",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Speech clients lazily
speech_client = None
tts_client = None

def get_speech_client():
    global speech_client
    if speech_client is None:
        speech_client = speech_v1.SpeechClient()
    return speech_client

def get_tts_client():
    global tts_client
    if tts_client is None:
        tts_client = texttospeech_v1.TextToSpeechClient()
    return tts_client


@app.get("/health")
async def health():
    """Health check"""
    try:
        # Test that clients can be initialized
        get_speech_client()
        get_tts_client()
        return {"status": "ok", "service": "stt-tts-only"}
    except Exception as e:
        return {"status": "error", "service": "stt-tts-only", "error": str(e)}, 500


@app.post("/api/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    language: Optional[str] = Form("en-US"),
):
    """
    Convert speech to text using Google Cloud Speech-to-Text
    """
    try:
        # Read audio file
        audio_content = await file.read()
        
        # Detect encoding from file extension
        file_ext = file.filename.split(".")[-1].lower() if file.filename else "webm"
        encoding_map = {
            "webm": speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            "mp3": speech_v1.RecognitionConfig.AudioEncoding.MP3,
            "wav": speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            "flac": speech_v1.RecognitionConfig.AudioEncoding.FLAC,
        }
        encoding = encoding_map.get(file_ext, speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS)
        
        # Configure recognition
        config = speech_v1.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=48000,
            language_code=language,
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        
        audio = speech_v1.RecognitionAudio(content=audio_content)
        
        # Perform transcription
        client = get_speech_client()
        response = client.recognize(config=config, audio=audio)
        
        # Extract transcript
        transcript = ""
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
        
        return {"text": transcript, "language": language}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")


@app.post("/api/tts")
async def text_to_speech(
    text: str = Form(...),
    terpene_id: Optional[str] = Form("terpenequeen"),
    speed: Optional[float] = Form(1.0),
):
    """
    Convert text to speech using Google Cloud Text-to-Speech
    Uses the terpene's specific voice
    Returns MP3 audio
    """
    try:
        from terpenes import get_terpene
        
        # Get terpene persona for voice
        terpene = get_terpene(terpene_id)
        google_voice = terpene["voice"]
        
        # Configure synthesis
        input_text = texttospeech_v1.SynthesisInput(text=text)
        
        # Voice configuration
        voice_config = texttospeech_v1.VoiceSelectionParams(
            language_code="-".join(google_voice.split("-")[:2]),  # e.g., "en-US"
            name=google_voice,
        )
        
        # Audio configuration
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3,
            speaking_rate=speed,
        )
        
        # Perform synthesis
        client = get_tts_client()
        response = client.synthesize_speech(
            input=input_text,
            voice=voice_config,
            audio_config=audio_config,
        )
        
        # Return audio content
        return Response(
            content=response.audio_content,
            media_type="audio/mpeg",
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")
