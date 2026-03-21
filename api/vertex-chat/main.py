"""
Cloud Run API for Terpene chat using Vertex AI + Google STT/TTS
Provides endpoints for text/audio chat with multiple terpene personas
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from google.cloud import aiplatform, speech_v1, texttospeech_v1
import base64
import os
import json
from typing import Optional, List, Dict
import io
import re
from terpenes import get_terpene, list_terpenes


def strip_fantasized_guest_dialogue_from_host(text: str) -> str:
    """
    If TerpeneQueen's turn includes scripted lines for other terpenes, keep only the host portion.
    """
    if not text or len(text) < 80:
        return text
    cut_patterns = [
        r"\n\s*\n(?:\*\*)?Greetings,\s*TerpeneQueen",
        r"\n\s*\nGreetings,\s*TerpeneQueen",
        r"\n\s*\nNamaste,\s*TerpeneQueen",
        r"\n\s*\nNamaste",
        r"\n\s*\nAh,\s*yes,\s*I know what\s+(?:Alpha-Pinene|Alpha\-Pinene|Pinene|Limonene|Linalool)",
        r"\n\s*\nWhile I(?:'|')m usually buzzing",
        r"\n\s*\n(?:\*\*)?(?:Ah, yes|Oh, yes),\s*I know what",
        r"\n\s*\nCiao\b",
        r"\n\s*\nBonjour\b",
    ]
    earliest = None
    for pat in cut_patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m and m.start() > 60:
            if earliest is None or m.start() < earliest:
                earliest = m.start()
    if earliest is not None:
        return text[:earliest].strip()
    return text

app = FastAPI(title="Terpene Vertex AI Chat API")

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

# Initialize Google Cloud clients
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "terpedia-489015")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")
DEFAULT_TTS_VOICE = os.getenv("DEFAULT_TTS_VOICE", "en-US-Neural2-F")
CUSTOM_VOICE_NAME = os.getenv("CUSTOM_VOICE_NAME")  # Susan Trapp's custom voice when available

# Initialize Vertex AI
aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_LOCATION)

# Initialize Speech clients
speech_client = speech_v1.SpeechClient()
tts_client = texttospeech_v1.TextToSpeechClient()


class ChatRequest(BaseModel):
    message: str
    active_terpenes: Optional[List[str]] = ["terpenequeen"]  # Which terpenes are in the panel
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    responses: List[Dict[str, str]]  # List of {terpene_id, response} pairs
    conversation_history: List[Dict[str, str]]


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "service": "terpene-vertex-chat",
        "project": GOOGLE_CLOUD_PROJECT,
        "location": GOOGLE_LOCATION,
    }


@app.get("/api/terpenes")
async def get_terpenes():
    """List all available terpene personas"""
    return {"terpenes": list_terpenes()}


def _panel_guests(active_terpenes: List[str]) -> List[str]:
    return [t for t in active_terpenes if t and t.lower() != "terpenequeen"]


def _last_assistant_terpene_id(conversation_history: List[Dict]) -> Optional[str]:
    for msg in reversed(conversation_history or []):
        if msg.get("role") == "assistant":
            tid = msg.get("terpene_id")
            if tid:
                return tid
    return None


def _topic_match_guest(message_lower: str, guests: List[str]) -> Optional[str]:
    if not guests:
        return None
    topic_keywords = {
        "linalool": ["lavender", "linalool", "floral", "sleep", "relax", "calm", "insomnia", "bath", "soothing", "sedative", "tranquil"],
        "limonene": ["limonene", "lemon", "citrus", "zest", "bright", "uplift", "energy", "mood", "orange"],
        "myrcene": ["myrcene", "muscle", "couch", "earthy", "mango"],
        "pinene": ["pinene", "pine", "forest", "focus", "alert", "memory", "clear"],
        "caryophyllene": ["caryophyllene", "pepper", "clove", "spicy", "stress"],
        "humulene": ["humulene", "hop", "beer", "appetite"],
        "terpinolene": ["terpinolene", "herbal", "mysterious"],
        "ocimene": ["ocimene", "basil", "sweet"],
        "bisabolol": ["bisabolol", "chamomile", "skin"],
        "geraniol": ["geraniol", "rose", "geranium"],
    }
    for tid in guests:
        for kw in topic_keywords.get(tid, []):
            if kw in message_lower:
                return tid
    for tid in guests:
        name = get_terpene(tid)["name"].lower()
        if len(name) > 3 and name in message_lower:
            return tid
    return None


def _pick_guest_round_robin(active_terpenes: List[str], conversation_history: List[Dict]) -> Optional[str]:
    guests = _panel_guests(active_terpenes)
    if not guests:
        return None
    n = sum(1 for m in (conversation_history or []) if m.get("role") == "user")
    return guests[n % len(guests)]


def detect_mentioned_terpenes(
    message: str,
    active_terpenes: List[str],
    conversation_history: Optional[List[Dict]] = None,
) -> List[str]:
    """
    Detect which terpenes are mentioned or should respond.
    With TerpeneQueen + guests, general messages alternate host/guests and use light topic routing.
    """
    conversation_history = conversation_history or []
    message_lower = message.lower()
    mentioned = []

    terpene_aliases = {
        "terpenequeen": ["terpenequeen", "susan", "susan trapp", "queen", "terpene queen"],
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
        terpene = get_terpene(terpene_id)
        terpene_name_lower = terpene["name"].lower()
        if terpene_name_lower in message_lower:
            mentioned.append(terpene_id)
            continue
        if terpene_id.lower() in message_lower:
            mentioned.append(terpene_id)
            continue
        aliases = terpene_aliases.get(terpene_id, [])
        for alias in aliases:
            if alias in message_lower:
                mentioned.append(terpene_id)
                break

    if not mentioned:
        if any(word in message_lower for word in ["all", "everyone", "panel", "you all", "what do you"]):
            return active_terpenes
        if len(active_terpenes) == 1:
            return active_terpenes

        guests = _panel_guests(active_terpenes)
        has_tq = any(t.lower() == "terpenequeen" for t in active_terpenes)

        if not guests:
            return [active_terpenes[0]]

        if has_tq and len(guests) >= 1:
            hit = _topic_match_guest(message_lower, guests)
            if hit:
                return [hit]
            science_cues = (
                "the science", "science behind", "about science", "scientific",
                "mechanism", "receptors", "receptor", "pathway", "biochemistry",
                "neurotransmitter", "gaba", "cb1", "cb2", "endocannabinoid",
                "how does it work", "how do they work", "at the molecular", "evidence for",
            )
            if any(cue in message_lower for cue in science_cues):
                nxt = _pick_guest_round_robin(active_terpenes, conversation_history)
                if nxt:
                    return [nxt]
            if not conversation_history:
                return ["terpenequeen"]
            last = _last_assistant_terpene_id(conversation_history)
            if last == "terpenequeen":
                nxt = _pick_guest_round_robin(active_terpenes, conversation_history)
                return [nxt] if nxt else [guests[0]]
            if last and last != "terpenequeen" and last in guests:
                return ["terpenequeen"]
            rr = _pick_guest_round_robin(active_terpenes, conversation_history)
            return [rr] if rr else [guests[0]]

        return [active_terpenes[0]]

    return list(set(mentioned))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with terpene personas. Multiple terpenes can be in the panel.
    Terpenes respond when mentioned or addressed.
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Determine which terpenes should respond
        responding_terpenes = detect_mentioned_terpenes(
            request.message,
            request.active_terpenes,
            request.conversation_history,
        )
        
        if not responding_terpenes:
            responding_terpenes = request.active_terpenes[:1]  # Fallback to first active
        
        responses = []
        updated_history = request.conversation_history.copy()
        
        # Add user message to history
        updated_history.append({"role": "user", "content": request.message})
        
        # Get responses from each mentioned terpene
        for terpene_id in responding_terpenes:
            terpene = get_terpene(terpene_id)
            system_prompt = terpene["system_prompt"]
            
            # Add context about other terpenes in the panel
            if len(request.active_terpenes) > 1:
                other_terpenes = [get_terpene(tid)["name"] for tid in request.active_terpenes if tid != terpene_id]
                panel_context = f"\n\nCONTEXT: You are in a panel discussion with: {', '.join(other_terpenes)}. You should respond when directly addressed or when your name/terpene is mentioned. Keep responses concise in a panel setting."
                panel_context += "\n\nOUTPUT: In this message, speak ONLY as your own persona. Do not write dialogue for other terpenes—they have separate messages."
                system_prompt = system_prompt + panel_context
            
            # Initialize Gemini model with terpene-specific system instruction
            model = GenerativeModel(
                model_name="gemini-2.0-flash-001",
                system_instruction=system_prompt,
            )
            
            # Build prompt with conversation history (including terpene_id for assistant messages)
            prompt_parts = []
            
            for msg in request.conversation_history:
                if msg["role"] == "user":
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    # Include terpene name if available
                    terpene_name = msg.get("terpene_id", "assistant")
                    if terpene_name != "assistant":
                        terpene_name = get_terpene(terpene_name)["name"]
                    prompt_parts.append(f"{terpene_name}: {msg['content']}")
            
            # Add current user message
            prompt_parts.append(f"User: {request.message}")
            prompt_parts.append(f"{terpene['name']}:")
            
            # Generate response
            response = model.generate_content("\n".join(prompt_parts))
            assistant_message = response.text
            if terpene_id == "terpenequeen" and len(
                [t for t in request.active_terpenes if t and t.lower() != "terpenequeen"]
            ) >= 1:
                assistant_message = strip_fantasized_guest_dialogue_from_host(assistant_message)
            
            # Add to responses and history
            responses.append({
                "terpene_id": terpene_id,
                "response": assistant_message
            })
            
            updated_history.append({
                "role": "assistant",
                "content": assistant_message,
                "terpene_id": terpene_id
            })
        
        return ChatResponse(
            responses=responses,
            conversation_history=updated_history,
        )
        
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}\n{traceback.format_exc()}")


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
        response = tts_client.synthesize_speech(
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


@app.post("/api/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    language: Optional[str] = Form("en-US"),
):
    """
    Convert speech to text using Google Cloud Speech-to-Text
    Accepts audio files (webm, mp3, wav, etc.)
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
            sample_rate_hertz=48000,  # Adjust based on your audio
            language_code=language,
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        
        audio = speech_v1.RecognitionAudio(content=audio_content)
        
        # Perform transcription
        response = speech_client.recognize(config=config, audio=audio)
        
        # Extract transcript
        transcript = ""
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
        
        return {"text": transcript, "language": language}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")




@app.post("/api/chat-audio")
async def chat_with_audio(
    audio_file: UploadFile = File(...),
    active_terpenes: Optional[str] = Form("terpenequeen"),  # JSON array string
    conversation_history: Optional[str] = Form(None),
    language: Optional[str] = Form("en-US"),
):
    """
    Complete audio chat: STT -> Vertex AI -> TTS
    Returns audio response
    """
    try:
        # Step 1: Speech to text
        audio_content = await audio_file.read()
        
        # Detect encoding
        file_ext = audio_file.filename.split(".")[-1].lower() if audio_file.filename else "webm"
        encoding_map = {
            "webm": speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            "mp3": speech_v1.RecognitionConfig.AudioEncoding.MP3,
            "wav": speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
        }
        encoding = encoding_map.get(file_ext, speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS)
        
        config = speech_v1.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=48000,
            language_code=language,
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        
        audio = speech_v1.RecognitionAudio(content=audio_content)
        stt_response = speech_client.recognize(config=config, audio=audio)
        
        if not stt_response.results:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        user_message = stt_response.results[0].alternatives[0].transcript
        
        # Step 2: Parse active terpenes
        try:
            active_terpenes_list = json.loads(active_terpenes) if isinstance(active_terpenes, str) else active_terpenes
        except Exception:
            active_terpenes_list = [active_terpenes] if isinstance(active_terpenes, str) else ["terpenequeen"]

        history_list: List[Dict] = []
        if conversation_history:
            try:
                history_list = json.loads(conversation_history)
            except Exception:
                history_list = []

        # Determine which terpenes should respond
        responding_terpenes = detect_mentioned_terpenes(user_message, active_terpenes_list, history_list)
        if not responding_terpenes:
            responding_terpenes = active_terpenes_list[:1]
        
        # Step 3: Chat with Vertex AI (get response from first responding terpene for audio)
        from vertexai.generative_models import GenerativeModel
        
        # For audio, use first responding terpene (can be enhanced to handle multiple)
        terpene_id = responding_terpenes[0]
        terpene = get_terpene(terpene_id)
        system_prompt = terpene["system_prompt"]
        
        # Add panel context if multiple terpenes
        if len(active_terpenes_list) > 1:
            other_terpenes = [get_terpene(tid)["name"] for tid in active_terpenes_list if tid != terpene_id]
            panel_context = f"\n\nCONTEXT: You are in a panel discussion with: {', '.join(other_terpenes)}. You should respond when directly addressed or when your name/terpene is mentioned. Keep responses concise in a panel setting."
            system_prompt = system_prompt + panel_context
        
        model = GenerativeModel(
            model_name="gemini-2.0-flash-001",
            system_instruction=system_prompt,
        )
        
        # Build prompt with conversation history
        prompt_parts = []
        
        # Parse and add conversation history if provided
        if conversation_history:
            try:
                history = json.loads(conversation_history)
                for msg in history:
                    if msg["role"] == "user":
                        prompt_parts.append(f"User: {msg['content']}")
                    elif msg["role"] == "assistant":
                        # Include terpene name if available
                        msg_terpene_id = msg.get("terpene_id", "assistant")
                        if msg_terpene_id != "assistant":
                            msg_terpene = get_terpene(msg_terpene_id)
                            prompt_parts.append(f"{msg_terpene['name']}: {msg['content']}")
                        else:
                            prompt_parts.append(f"Assistant: {msg['content']}")
            except:
                pass
        
        # Add current user message
        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append(f"{terpene['name']}:")
        
        # Generate response
        ai_response = model.generate_content("\n".join(prompt_parts))
        assistant_text = ai_response.text
        
        # Step 4: Text to speech (using terpene's voice)
        terpene_voice = terpene["voice"]
        input_text = texttospeech_v1.SynthesisInput(text=assistant_text)
        voice_config = texttospeech_v1.VoiceSelectionParams(
            language_code="-".join(terpene_voice.split("-")[:2]),
            name=terpene_voice,
        )
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3,
            speaking_rate=1.0,
        )
        
        tts_response = tts_client.synthesize_speech(
            input=input_text,
            voice=voice_config,
            audio_config=audio_config,
        )
        
        # Return audio with terpene info in headers
        return Response(
            content=tts_response.audio_content,
            media_type="audio/mpeg",
            headers={
                "X-User-Transcript": user_message,
                "X-Assistant-Text": assistant_text,
                "X-Terpene-ID": terpene_id,
                "X-Assistant-Text": assistant_text,
            },
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio chat failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
