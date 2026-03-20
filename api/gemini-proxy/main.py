"""
Cloud Function for Terpene Chat - Vertex AI + STT/TTS
Uses service account authentication (no API key needed)
"""
import functions_framework
from flask import Request, jsonify, make_response, request as flask_request
import os
import json
from typing import List, Dict, Optional
import base64

# Google Cloud project and location
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "terpedia-489015")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# Initialize Vertex AI (uses service account from Cloud Function)
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
    from google.cloud import speech_v1, texttospeech_v1
    aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_LOCATION)
    VERTEX_AI_AVAILABLE = True
    SPEECH_AVAILABLE = True
except Exception as e:
    VERTEX_AI_AVAILABLE = False
    SPEECH_AVAILABLE = False
    print(f"Warning: Google Cloud services not available: {e}")

# Initialize Speech clients lazily
speech_client = None
tts_client = None

def get_speech_client():
    global speech_client
    if speech_client is None and SPEECH_AVAILABLE:
        speech_client = speech_v1.SpeechClient()
    return speech_client

def get_tts_client():
    global tts_client
    if tts_client is None and SPEECH_AVAILABLE:
        tts_client = texttospeech_v1.TextToSpeechClient()
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


# Allowed origins (only our chat interface)
ALLOWED_ORIGINS = [
    "https://tersona.terpedia.com",
    "https://terpedia.github.io",  # GitHub Pages fallback
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Local development
]

def validate_origin(request: Request) -> bool:
    """Validate that request comes from allowed origin"""
    origin = request.headers.get("Origin") or request.headers.get("Referer", "")
    
    # Extract domain from referer if origin not present
    if not origin.startswith("http"):
        return False
    
    # Check if origin matches allowed list
    for allowed in ALLOWED_ORIGINS:
        if origin.startswith(allowed):
            return True
    
    return False


@functions_framework.http
def terpene_api(request: Request):
    """
    Main entry point - routes to chat, stt, or tts based on path
    """
    path = request.path.strip('/')
    
    if path == 'chat' or path == '':
        return chat(request)
    elif path == 'stt':
        return stt(request)
    elif path == 'tts':
        return tts(request)
    elif path == 'health':
        return jsonify({"status": "ok", "service": "terpene-api"}), 200
    else:
        return jsonify({"error": "Not found"}), 404


def chat(request: Request):
    """
    Proxy Gemini API calls
    POST /chat
    Body: {
        "message": str,
        "active_terpenes": List[str],
        "conversation_history": List[Dict]
    }
    """
    # CORS headers
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        if validate_origin(request):
            return make_response("", 204, {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Max-Age": "3600",
            })
        return make_response("", 403, {})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
    
    # Validate origin - only allow requests from our chat interface
    if not validate_origin(request):
        return jsonify({"error": "Forbidden: Request not from allowed origin"}), 403, {
            "Access-Control-Allow-Origin": "null"
        }
    
    
    try:
        data = request.get_json()
        message = data.get("message", "")
        active_terpenes = data.get("active_terpenes", ["terpenequeen"])
        conversation_history = data.get("conversation_history", [])
        
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
            
            # Build conversation for Gemini
            contents = []
            
            # Add system instruction as first user message (Gemini format)
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I'll stay in character."}]
            })
            
            # Add conversation history
            for msg in conversation_history:
                if msg.get("role") == "user":
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg["content"]}]
                    })
                elif msg.get("role") == "assistant":
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg["content"]}]
                    })
            
            # Add current message
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })
            
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
        
        origin = request.headers.get("Origin", "")
        return jsonify({
            "responses": responses,
            "conversation_history": updated_history
        }), 200, {
            "Access-Control-Allow-Origin": origin if validate_origin(request) else "null",
            "Content-Type": "application/json"
        }
        
    except Exception as e:
        origin = request.headers.get("Origin", "")
        return jsonify({"error": str(e)}), 500, {
            "Access-Control-Allow-Origin": origin if validate_origin(request) else "null"
        }


@functions_framework.http
def stt(request: Request):
    """
    Speech-to-Text endpoint
    POST /stt
    Body: multipart/form-data with audio file
    """
    # CORS
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        if validate_origin(request):
            return make_response("", 204, {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            })
        return make_response("", 403, {})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
    
    if not validate_origin(request):
        return jsonify({"error": "Forbidden: Request not from allowed origin"}), 403
    
    if not SPEECH_AVAILABLE:
        return jsonify({"error": "Speech-to-Text not available"}), 500
    
    try:
        # Get audio file from form data
        if 'file' not in flask_request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = flask_request.files['file']
        audio_content = audio_file.read()
        language = flask_request.form.get('language', 'en-US')
        
        # Detect encoding from file extension
        file_ext = audio_file.filename.split(".")[-1].lower() if audio_file.filename else "webm"
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
        
        origin = request.headers.get("Origin", "")
        return jsonify({"text": transcript, "language": language}), 200, {
            "Access-Control-Allow-Origin": origin if validate_origin(request) else "null"
        }
        
    except Exception as e:
        origin = request.headers.get("Origin", "")
        return jsonify({"error": str(e)}), 500, {
            "Access-Control-Allow-Origin": origin if validate_origin(request) else "null"
        }


@functions_framework.http
def tts(request: Request):
    """
    Text-to-Speech endpoint
    POST /tts
    Body: form-data with text, terpene_id, speed
    Returns: MP3 audio
    """
    # CORS
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        if validate_origin(request):
            return make_response("", 204, {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            })
        return make_response("", 403, {})
    
    if request.method != "POST":
        return make_response("Method not allowed", 405)
    
    if not validate_origin(request):
        return make_response("Forbidden", 403)
    
    if not SPEECH_AVAILABLE:
        return make_response("Text-to-Speech not available", 500)
    
    try:
        from terpenes import get_terpene
        
        # Get form data
        text = flask_request.form.get('text', '')
        terpene_id = flask_request.form.get('terpene_id', 'terpenequeen')
        speed = float(flask_request.form.get('speed', 1.0))
        
        if not text:
            return make_response("No text provided", 400)
        
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
        
        origin = request.headers.get("Origin", "")
        return make_response(
            response.audio_content,
            200,
            {
                "Content-Type": "audio/mpeg",
                "Access-Control-Allow-Origin": origin if validate_origin(request) else "null"
            }
        )
        
    except Exception as e:
        origin = request.headers.get("Origin", "")
        return jsonify({"error": str(e)}), 500, {
            "Access-Control-Allow-Origin": origin if validate_origin(request) else "null"
        }
