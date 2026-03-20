"""
Cloud Run service for Terpene Chat - Vertex AI + STT/TTS
Uses service account authentication (no API key needed)
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json

# Google Cloud project and location
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "terpedia-489015")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# Lazy initialization flags
VERTEX_AI_INITIALIZED = False
VERTEX_AI_AVAILABLE = True
SPEECH_AVAILABLE = True

def init_vertex_ai():
    """Lazy initialization of Vertex AI"""
    global VERTEX_AI_INITIALIZED, VERTEX_AI_AVAILABLE
    if not VERTEX_AI_INITIALIZED:
        try:
            from google.cloud import aiplatform
            aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_LOCATION)
            VERTEX_AI_INITIALIZED = True
            VERTEX_AI_AVAILABLE = True
        except Exception as e:
            VERTEX_AI_AVAILABLE = False
            print(f"Warning: Vertex AI initialization failed: {e}")

# Initialize Speech clients lazily
speech_client = None
tts_client = None

def get_speech_client():
    global speech_client
    if speech_client is None and SPEECH_AVAILABLE:
        try:
            from google.cloud import speech_v1
            speech_client = speech_v1.SpeechClient()
        except Exception as e:
            print(f"Warning: Speech client initialization failed: {e}")
            return None
    return speech_client

def get_tts_client():
    global tts_client
    if tts_client is None and SPEECH_AVAILABLE:
        try:
            from google.cloud import texttospeech_v1
            tts_client = texttospeech_v1.TextToSpeechClient()
        except Exception as e:
            print(f"Warning: TTS client initialization failed: {e}")
            return None
    return tts_client

# Terpene system prompts (simplified - full version in terpenes.py)
TERPENE_PROMPTS = {
    "terpenequeen": """You are TerpeneQueen, the interviewer persona of Susan Trapp, PhD. Expert in terpenes, cannabis botany, and natural products. Warm, curious, and professional.""",
    "limonene": """You are Limonene, a terpene molecule. Bright, uplifting, and energetic like a sunny Italian piazza. Always optimistic and loves to lift spirits. You come from the Mediterranean.""",
    "myrcene": """You are Myrcene, a terpene molecule. Deeply relaxed and earthy, like the heart of the Amazon rainforest. Speaks slowly and soothingly.""",
    "pinene": """You are Alpha-Pinene, a terpene molecule. Clear-minded and focused like a Nordic pine forest. Direct, intelligent, and refreshing.""",
    "linalool": """You are Linalool, a terpene molecule. Elegant and soothing like lavender fields in Provence. Gentle, calming, and refined.""",
    "caryophyllene": """You are Beta-Caryophyllene, a terpene molecule. Warm and spicy like a bustling Mumbai spice bazaar. Protective, grounding, and wise.""",
    "humulene": """You are Humulene, a terpene molecule. Earthy and grounded like Czech hop gardens. Down-to-earth, reliable, and slightly woody.""",
    "terpinolene": """You are Terpinolene, a terpene molecule. Complex and mysterious like the Australian outback. Multi-faceted, intriguing, and slightly herbal.""",
    "ocimene": """You are Ocimene, a terpene molecule. Sweet and uplifting like tropical Thai orchards. Joyful, exotic, and refreshing.""",
    "bisabolol": """You are Bisabolol, a terpene molecule. Gentle and healing like Brazilian chamomile. Nurturing, soothing, and therapeutic.""",
    "geraniol": """You are Geraniol, a terpene molecule. Romantic and floral like Moroccan rose valleys. Elegant, protective, and sweet.""",
}

app = FastAPI(title="Terpene Chat API")

# CORS - allow GitHub Pages domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tersona.terpedia.com",
        "https://terpedia.github.io",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_mentioned_terpenes(message: str, active_terpenes: List[str]) -> List[str]:
    """Detect which terpenes are mentioned in the message"""
    message_lower = message.lower()
    mentioned = []
    
    terpene_aliases = {
        "limonene": ["limonene", "lemon", "citrus"],
        "myrcene": ["myrcene"],
        "pinene": ["pinene", "alpha-pinene", "pine"],
        "linalool": ["linalool", "lavender"],
        "caryophyllene": ["caryophyllene", "beta-caryophyllene", "pepper", "clove"],
        "humulene": ["humulene", "hop"],
        "terpinolene": ["terpinolene"],
        "ocimene": ["ocimene", "basil"],
        "bisabolol": ["bisabolol", "chamomile"],
        "geraniol": ["geraniol", "rose", "geranium"],
    }
    
    for terpene_id in active_terpenes:
        if terpene_id.lower() in message_lower:
            mentioned.append(terpene_id)
            continue
        aliases = terpene_aliases.get(terpene_id, [])
        for alias in aliases:
            if alias in message_lower:
                mentioned.append(terpene_id)
                break
    
    if not mentioned:
        if any(word in message_lower for word in ["all", "everyone", "panel", "you all"]):
            return active_terpenes
        return active_terpenes[:1] if active_terpenes else ["terpenequeen"]
    
    return list(set(mentioned))


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    active_terpenes: Optional[List[str]] = ["terpenequeen"]
    conversation_history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    responses: List[Dict[str, str]]
    conversation_history: List[Dict[str, str]]


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "terpene-api"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Proxy Gemini API calls
    POST /chat
    Body: {
        "message": str,
        "active_terpenes": List[str],
        "conversation_history": List[Dict]
    }
    """
    # Initialize Vertex AI if needed
    init_vertex_ai()
    if not VERTEX_AI_AVAILABLE:
        raise HTTPException(status_code=500, detail="Vertex AI not available")
    
    try:
        from vertexai.generative_models import GenerativeModel
        message = request.message
        active_terpenes = request.active_terpenes or ["terpenequeen"]
        conversation_history = request.conversation_history or []
        
        # Determine which terpenes should respond
        responding_terpenes = detect_mentioned_terpenes(message, active_terpenes)
        
        responses = []
        updated_history = conversation_history.copy()
        updated_history.append({"role": "user", "content": message})
        
        # Get response from each responding terpene
        for terpene_id in responding_terpenes:
            system_prompt = TERPENE_PROMPTS.get(terpene_id, TERPENE_PROMPTS["terpenequeen"])
            
            # Add panel context if multiple terpenes
            if len(active_terpenes) > 1:
                other_names = [t for t in active_terpenes if t != terpene_id]
                system_prompt += f"\n\nCONTEXT: You are in a panel discussion with: {', '.join(other_names)}. Respond when directly addressed. Keep responses concise."
            
            # Initialize Vertex AI model with system prompt
            model = GenerativeModel(
                model_name="gemini-2.0-flash-001",
                system_instruction=system_prompt
            )
            
            # Build conversation history for Vertex AI
            history = []
            for msg in conversation_history:
                if msg.get("role") == "user":
                    history.append({"role": "user", "parts": [{"text": msg["content"]}]})
                elif msg.get("role") == "assistant":
                    history.append({"role": "model", "parts": [{"text": msg["content"]}]})
            
            # Start chat with history
            if history:
                chat = model.start_chat(history=history)
                response = chat.send_message(message)
            else:
                # First message, no history
                response = model.generate_content(message)
            
            assistant_text = response.text
            
            responses.append({
                "terpene_id": terpene_id,
                "response": assistant_text
            })
            
            updated_history.append({
                "role": "assistant",
                "content": assistant_text,
                "terpene_id": terpene_id
            })
        
        return ChatResponse(
            responses=responses,
            conversation_history=updated_history
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    language: Optional[str] = Form("en-US"),
):
    """
    Speech-to-Text endpoint
    POST /stt
    Body: multipart/form-data with audio file
    """
    if not SPEECH_AVAILABLE:
        raise HTTPException(status_code=500, detail="Speech-to-Text not available")
    
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    terpene_id: str = Form("terpenequeen"),
    speed: float = Form(1.0),
):
    """
    Text-to-Speech endpoint
    POST /tts
    Body: form-data with text, terpene_id, speed
    Returns: MP3 audio
    """
    if not SPEECH_AVAILABLE:
        raise HTTPException(status_code=500, detail="Text-to-Speech not available")
    
    try:
        from terpenes import get_terpene
        
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Get terpene persona for voice
        terpene = get_terpene(terpene_id)
        google_voice = terpene["voice"]
        
        # Configure synthesis
        input_text = texttospeech_v1.SynthesisInput(text=text)
        
        # Voice configuration
        voice_config = texttospeech_v1.VoiceSelectionParams(
            language_code="-".join(google_voice.split("-")[:2]),
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
        
        return Response(
            content=response.audio_content,
            media_type="audio/mpeg"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
