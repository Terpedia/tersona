"""
FastAPI bridge for Google Cloud Speech (STT) and Text-to-Speech (TTS)
Provides OpenAI-compatible endpoints that LibreChat can use
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from pydantic import BaseModel
from google.cloud import speech_v1, texttospeech_v1
import base64
import os
from typing import Optional

app = FastAPI(title="Google Speech Bridge for LibreChat")

# Initialize Google Cloud clients
speech_client = speech_v1.SpeechClient()
tts_client = texttospeech_v1.TextToSpeechClient()

# Configuration from environment
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
DEFAULT_TTS_VOICE = os.getenv("DEFAULT_TTS_VOICE", "en-US-Neural2-A")
CUSTOM_VOICE_NAME = os.getenv("CUSTOM_VOICE_NAME")  # Susan Trapp's custom voice when available


class TTSRequest(BaseModel):
    """OpenAI-compatible TTS request"""
    model: str  # e.g., "tts-1", "tts-1-hd" (we'll ignore and use Google)
    input: str  # Text to synthesize
    voice: str  # e.g., "alloy", "echo" - we'll map these to Google voices
    response_format: Optional[str] = "mp3"
    speed: Optional[float] = 1.0


# Voice mapping: OpenAI voice names -> Google voice names
VOICE_MAP = {
    "alloy": "en-US-Neural2-A",
    "echo": "en-US-Neural2-C",
    "fable": "en-US-Neural2-D",
    "onyx": "en-US-Neural2-I",
    "nova": "en-US-Neural2-F",
    "shimmer": "en-US-Neural2-H",
    "susan": CUSTOM_VOICE_NAME or "en-US-Neural2-F",  # Use custom voice when available
}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "google-speech-bridge"}


@app.post("/v1/audio/transcriptions")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json")
):
    """
    Speech-to-Text endpoint (OpenAI Whisper compatible)
    Converts audio to text using Google Cloud Speech-to-Text
    """
    try:
        # Read audio file
        audio_content = await file.read()
        
        # Configure recognition
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code=language or "en-US",
            enable_automatic_punctuation=True,
            model="latest_long",  # Use latest model
        )
        
        audio = speech_v1.RecognitionAudio(content=audio_content)
        
        # Perform transcription
        response = speech_client.recognize(config=config, audio=audio)
        
        # Extract transcript
        transcript = ""
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
        
        # Return in OpenAI format
        if response_format == "verbose_json":
            return {
                "text": transcript,
                "task": "transcribe",
                "language": language or "en",
                "duration": 0,  # Google doesn't return duration easily
            }
        else:
            return {"text": transcript}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/v1/audio/speech")
async def synthesize_speech(request: TTSRequest):
    """
    Text-to-Speech endpoint (OpenAI TTS compatible)
    Converts text to speech using Google Cloud Text-to-Speech
    """
    try:
        # Map voice name
        google_voice = VOICE_MAP.get(request.voice, DEFAULT_TTS_VOICE)
        
        # Configure synthesis
        input_text = texttospeech_v1.SynthesisInput(text=request.input)
        
        # Voice configuration
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=google_voice.split("-")[0] + "-" + google_voice.split("-")[1],
            name=google_voice,
        )
        
        # Audio configuration
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3,
            speaking_rate=request.speed,
        )
        
        # Perform synthesis
        response = tts_client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config,
        )
        
        # Return audio content
        return Response(
            content=response.audio_content,
            media_type="audio/mpeg",
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with info"""
    return {
        "service": "Google Speech Bridge for LibreChat",
        "endpoints": {
            "stt": "/v1/audio/transcriptions",
            "tts": "/v1/audio/speech",
            "health": "/health"
        },
        "custom_voice_configured": CUSTOM_VOICE_NAME is not None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
