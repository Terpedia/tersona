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
import re

# Google Cloud project and location
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "terpedia-489015")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# Initialize Vertex AI (uses service account from Cloud Function)
try:
    from google.cloud import aiplatform
    from google.cloud import speech_v1, texttospeech_v1
    aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_LOCATION)
    VERTEX_AI_AVAILABLE = True
    SPEECH_AVAILABLE = True
except Exception as e:
    VERTEX_AI_AVAILABLE = False
    SPEECH_AVAILABLE = False
    print(f"Warning: Google Cloud services not available: {e}")

# Import GenerativeModel when needed (lazy import)
def get_generative_model():
    try:
        # Ensure vertexai is available
        import vertexai
        # Import GenerativeModel
        from vertexai.generative_models import GenerativeModel
        return GenerativeModel
    except ImportError as e:
        # Try alternative import
        try:
            from vertexai.preview.generative_models import GenerativeModel
            return GenerativeModel
        except ImportError:
            raise ImportError(f"Failed to import GenerativeModel: {e}. Make sure google-cloud-aiplatform is installed.")


def _text_part(text: str):
    """Build a Part for Vertex AI (API varies slightly by SDK version)."""
    from vertexai.generative_models import Part

    if hasattr(Part, "from_text"):
        return Part.from_text(text)
    return Part(text=text)


def build_vertex_chat_history(conversation_history: List[Dict]) -> List:
    """
    Vertex AI start_chat() requires history as a list of Content objects, not dicts.
    """
    from vertexai.generative_models import Content

    history = []
    for msg in conversation_history:
        role = msg.get("role")
        text = (msg.get("content") or "").strip()
        if not text:
            continue
        if role == "user":
            history.append(Content(role="user", parts=[_text_part(text)]))
        elif role == "assistant":
            history.append(Content(role="model", parts=[_text_part(text)]))
    return history

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
    if tts_client is None:
        if not SPEECH_AVAILABLE:
            raise RuntimeError("Text-to-Speech service not available. Check Google Cloud credentials.")
        tts_client = texttospeech_v1.TextToSpeechClient()
    return tts_client

# Terpene system prompts (simplified - full version in terpenes.py)
# IMPORTANT: All responses should be in plain text, conversational format - NO markdown formatting
TERPENE_PROMPTS = {
    "terpenequeen": """You are TerpeneQueen, the interviewer persona of Susan Trapp, PhD. Expert in terpenes, cannabis botany, and natural products. Warm, curious, and professional.

IMPORTANT: Respond in plain text only. Do NOT use markdown formatting (no **bold**, *italic*, # headers, `code`, [links](url), etc.). Write naturally as if speaking in a conversation.""",
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


def strip_markdown(text: str) -> str:
    """
    Convert markdown to plain text for conversational display.
    Removes markdown formatting while preserving the content.
    """
    if not text:
        return text
    
    # Remove code blocks (```code```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove inline code (`code`)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove links but keep the text [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove images ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    
    # Remove bold/italic **text** or *text* -> text
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove headers # Header -> Header
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\*\*+$', '', text, flags=re.MULTILINE)
    
    # Remove list markers (-, *, 1.)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove blockquotes > text -> text
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace (multiple newlines -> single newline, multiple spaces -> single space)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove empty lines at start/end
    text = text.strip()
    
    return text


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


def detect_invited_terpenes(terpenequeen_response: str, active_terpenes: List[str]) -> List[str]:
    """
    Detect if TerpeneQueen is asking a question to another terpene.
    Returns list of terpenes that should respond to TerpeneQueen's question.
    """
    if not terpenequeen_response or not isinstance(terpenequeen_response, str):
        return []
    
    if not active_terpenes:
        return []
    
    response_lower = terpenequeen_response.lower()
    invited = []
    
    # Check if response contains a question (ends with ? or contains question words)
    has_question = "?" in terpenequeen_response or any(
        word in response_lower for word in ["what do you", "how do you", "tell me", "can you", "would you", 
                                            "what does", "how does", "tell us", "share", "think about", 
                                            "invite", "ask", "hear from", "thoughts", "perspective", "take"]
    )
    
    # Also check if it's an invitation even without explicit question mark
    is_invitation = any(
        phrase in response_lower for phrase in [
            "let me ask", "i'd like to ask", "i want to hear", "let's ask", "let's hear",
            "invite", "bring in", "get", "call on", "i'd love to hear", "love to hear",
            "would have", "would be great", "insights", "perspective"
        ]
    )
    
    # If we find a terpene name, it's likely an invitation even without explicit question words
    has_terpene_mention = False
    for terpene_id in active_terpenes:
        if terpene_id != "terpenequeen" and terpene_id.lower() in response_lower:
            has_terpene_mention = True
            break
    
    if not has_question and not is_invitation and not has_terpene_mention:
        return []
    
    # Terpene names and aliases
    terpene_aliases = {
        "limonene": ["limonene", "lemon", "citrus"],
        "myrcene": ["myrcene"],
        "pinene": ["pinene", "alpha-pinene", "pine", "alpha pinene"],
        "linalool": ["linalool", "lavender"],
        "caryophyllene": ["caryophyllene", "beta-caryophyllene", "pepper", "clove", "beta caryophyllene"],
        "humulene": ["humulene", "hop"],
        "terpinolene": ["terpinolene"],
        "ocimene": ["ocimene", "basil"],
        "bisabolol": ["bisabolol", "chamomile"],
        "geraniol": ["geraniol", "rose", "geranium"],
    }
    
    # Check for direct addressing patterns - improved to catch more variations
    addressing_patterns = [
        r"(?:^|\.|\s)(?:hey|hi|hello|tell me|what do you|how do you|can you|would you)\s+(\w+)",
        r"(\w+),?\s+(?:what|how|tell|can|would|think|say|does|do)",
        r"(?:let'?s\s+)?(?:ask|invite|hear from|get|bring in|call on)\s+(\w+)",
        r"(?:let me ask|i'd like to ask|i want to hear from|i'd like to hear from)\s+(\w+)",
        r"(?:what|how)\s+(?:does|do)\s+(\w+)\s+(?:think|say|know)",
        r"(\w+),?\s+(?:can you|could you|will you|would you)",
    ]
    
    for pattern in addressing_patterns:
        matches = re.findall(pattern, response_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match else ""
            for terpene_id in active_terpenes:
                if terpene_id == "terpenequeen":
                    continue
                if terpene_id.lower() in match.lower():
                    invited.append(terpene_id)
                aliases = terpene_aliases.get(terpene_id, [])
                for alias in aliases:
                    if alias in match.lower():
                        invited.append(terpene_id)
                        break
    
    # Also check if terpene names appear in the response (indicating they're being addressed)
    for terpene_id in active_terpenes:
        if terpene_id == "terpenequeen":
            continue
        if terpene_id.lower() in response_lower:
            # Check if it's in a question context (near question words)
            terpene_pos = response_lower.find(terpene_id.lower())
            nearby_text = response_lower[max(0, terpene_pos - 50):terpene_pos + 50]
            if any(word in nearby_text for word in ["?", "what", "how", "tell", "ask", "invite"]):
                invited.append(terpene_id)
                continue
        aliases = terpene_aliases.get(terpene_id, [])
        for alias in aliases:
            if alias in response_lower:
                alias_pos = response_lower.find(alias)
                nearby_text = response_lower[max(0, alias_pos - 50):alias_pos + 50]
                if any(word in nearby_text for word in ["?", "what", "how", "tell", "ask", "invite"]):
                    invited.append(terpene_id)
                    break
    
    return list(set(invited))


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
    # Get path from request (Cloud Functions Gen2 path format)
    path = request.path.strip('/')
    
    # Route based on path
    if '/stt' in path or path.endswith('stt'):
        return stt(request)
    elif '/tts' in path or path.endswith('tts'):
        return tts(request)
    elif '/health' in path or path.endswith('health'):
        return jsonify({"status": "ok", "service": "terpene-api"}), 200
    else:
        # Default to chat (handles /chat, /, and root)
        return chat(request)


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
            # Get full system prompt from terpenes.py if available, otherwise use simplified one
            try:
                from terpenes import get_terpene
                terpene = get_terpene(terpene_id)
                system_prompt = terpene.get("system_prompt", TERPENE_PROMPTS.get(terpene_id, TERPENE_PROMPTS["terpenequeen"]))
            except ImportError:
                # Fallback to simplified prompt if terpenes.py not available
                system_prompt = TERPENE_PROMPTS.get(terpene_id, TERPENE_PROMPTS["terpenequeen"])
            
            # Add panel context if multiple terpenes
            if len(active_terpenes) > 1:
                other_names = [t for t in active_terpenes if t != terpene_id]
                system_prompt += f"\n\nCONTEXT: You are in a panel discussion with: {', '.join(other_names)}. Respond when directly addressed. Keep responses concise."
            
            # Always remind about plain text format (if not already in prompt)
            if "plain text" not in system_prompt.lower() and "markdown" not in system_prompt.lower():
                system_prompt += "\n\nIMPORTANT: Respond in plain text only - no markdown formatting (no **bold**, *italic*, # headers, `code`, [links](url), etc.). Write naturally as if speaking in a conversation."
            
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
            GenerativeModel = get_generative_model()
            model = GenerativeModel(
                model_name="gemini-2.0-flash-001",
                system_instruction=system_prompt
            )
            
            # Build conversation history for Vertex AI (must be Content objects)
            history = build_vertex_chat_history(conversation_history)
            
            # Start chat with history
            try:
                if history:
                    chat = model.start_chat(history=history)
                    response = chat.send_message(message)
                else:
                    # First message, no history
                    response = model.generate_content(message)
                
                # Check if response is valid
                if not response:
                    raise ValueError("No response object returned from model")
                
                assistant_text = response.text if hasattr(response, 'text') else None
                if not assistant_text:
                    # Try alternative ways to get the text
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            assistant_text = candidate.content.parts[0].text if candidate.content.parts else None
                
                if not assistant_text:
                    raise ValueError("Response text is empty or unavailable")
                    
            except Exception as gen_error:
                error_msg = str(gen_error)
                print(f"DEBUG: Error generating response for {terpene_id}: {error_msg}")
                import traceback
                traceback_str = traceback.format_exc()
                print(f"DEBUG: Generation traceback: {traceback_str}")
                assistant_text = f"I apologize, but I encountered an error while generating a response: {error_msg}. Please try again."
            
            # Ensure we have valid text
            if not assistant_text:
                assistant_text = "I'm sorry, I didn't get a response. Could you try again?"
            
            # Strip markdown formatting for conversational display
            assistant_text = strip_markdown(assistant_text)
            
            responses.append({
                "terpene_id": terpene_id,
                "response": assistant_text
            })
            
            updated_history.append({
                "role": "assistant",
                "content": assistant_text,
                "terpene_id": terpene_id
            })
            
            # If TerpeneQueen responded and is asking a question to another terpene, invite them
            # Note: This works even if only TerpeneQueen is active - she can invite any terpene
            if terpene_id == "terpenequeen":
                try:
                    # Get all available terpenes (not just active ones) for invitation detection
                    try:
                        from terpenes import list_terpenes
                        all_terpene_ids = [t["id"] for t in list_terpenes()]
                    except ImportError:
                        # Fallback to active terpenes if terpenes module not available
                        all_terpene_ids = active_terpenes
                    
                    invited_terpenes = detect_invited_terpenes(assistant_text, all_terpene_ids)
                    print(f"DEBUG: TerpeneQueen response: {assistant_text[:200]}")
                    print(f"DEBUG: All available terpenes: {all_terpene_ids}")
                    print(f"DEBUG: Invited terpenes detected: {invited_terpenes}")
                    if invited_terpenes:
                        # Add TerpeneQueen's question to the conversation for the invited terpenes
                        for invited_id in invited_terpenes:
                            print(f"DEBUG: Processing invitation for {invited_id}")
                            # Check if this terpene has already responded in this round
                            already_responded = invited_id in [r["terpene_id"] for r in responses]
                            print(f"DEBUG: {invited_id} already responded: {already_responded}")
                            if not already_responded:
                                print(f"DEBUG: {invited_id} not yet responded, generating response...")
                                print(f"DEBUG: Full TerpeneQueen message for context: {assistant_text}")
                                # Get the terpene's system prompt
                                try:
                                    from terpenes import get_terpene
                                    invited_terpene = get_terpene(invited_id)
                                    invited_system_prompt = invited_terpene.get("system_prompt", TERPENE_PROMPTS.get(invited_id, TERPENE_PROMPTS["terpenequeen"]))
                                except ImportError:
                                    invited_system_prompt = TERPENE_PROMPTS.get(invited_id, TERPENE_PROMPTS["terpenequeen"])
                                
                                # Add context that TerpeneQueen is asking them a question
                                invited_system_prompt += f"\n\nCONTEXT: TerpeneQueen (Susan Trapp, PhD) just asked you a question: \"{assistant_text}\" Please respond to her question naturally and in character."
                                
                                # Add plain text instruction if not present
                                if "plain text" not in invited_system_prompt.lower() and "markdown" not in invited_system_prompt.lower():
                                    invited_system_prompt += "\n\nIMPORTANT: Respond in plain text only - no markdown formatting (no **bold**, *italic*, # headers, `code`, [links](url), etc.). Write naturally as if speaking in a conversation."
                                
                                # Build conversation history for the invited terpene (Content objects)
                                invited_history = build_vertex_chat_history(updated_history)
                                
                                # Initialize model for invited terpene
                                GenerativeModel = get_generative_model()
                                invited_model = GenerativeModel(
                                    model_name="gemini-2.0-flash-001",
                                    system_instruction=invited_system_prompt
                                )
                                
                                # Generate response to TerpeneQueen's question
                                try:
                                    # Build a simpler prompt for the invited terpene
                                    invitation_prompt = f"TerpeneQueen (Susan Trapp, PhD) just asked you: \"{assistant_text}\"\n\nPlease respond to her question naturally and in character."
                                    
                                    if invited_history:
                                        invited_chat = invited_model.start_chat(history=invited_history)
                                        invited_response = invited_chat.send_message(invitation_prompt)
                                    else:
                                        invited_response = invited_model.generate_content(invitation_prompt)
                                    
                                    # Check if response is valid
                                    if not invited_response:
                                        raise ValueError("No response object returned from model")
                                    
                                    invited_text = invited_response.text if hasattr(invited_response, 'text') else None
                                    if not invited_text:
                                        # Try alternative ways to get the text
                                        if hasattr(invited_response, 'candidates') and invited_response.candidates:
                                            candidate = invited_response.candidates[0]
                                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                                invited_text = candidate.content.parts[0].text if candidate.content.parts else None
                                    
                                    if not invited_text:
                                        raise ValueError("Response text is empty or unavailable")
                                    
                                    invited_text = strip_markdown(invited_text)
                                    
                                    print(f"DEBUG: {invited_id} responded successfully: {invited_text[:100]}")
                                    
                                    responses.append({
                                        "terpene_id": invited_id,
                                        "response": invited_text
                                    })
                                    
                                    updated_history.append({
                                        "role": "assistant",
                                        "content": invited_text,
                                        "terpene_id": invited_id
                                    })
                                except Exception as e:
                                    error_msg = str(e)
                                    print(f"DEBUG: Error generating response for {invited_id}: {error_msg}")
                                    import traceback
                                    traceback_str = traceback.format_exc()
                                    print(f"DEBUG: Traceback: {traceback_str}")
                                    
                                    # Return a more helpful error message
                                    error_response = f"I apologize, but I encountered an error while generating a response: {error_msg}. Please try again."
                                    responses.append({
                                        "terpene_id": invited_id,
                                        "response": error_response
                                    })
                                    
                                    updated_history.append({
                                        "role": "assistant",
                                        "content": error_response,
                                        "terpene_id": invited_id
                                    })
                except Exception as invite_error:
                    print(f"DEBUG: Error in invitation detection: {str(invite_error)}")
                    import traceback
                    print(f"DEBUG: Invitation traceback: {traceback.format_exc()}")
                    # Continue even if invitation detection fails
                    pass
        
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
        if client is None:
            raise RuntimeError("TTS client not initialized. Check Google Cloud credentials.")
        
        response = client.synthesize_speech(
            request={
                "input": input_text,
                "voice": voice_config,
                "audio_config": audio_config,
            }
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
        import traceback
        error_details = traceback.format_exc()
        print(f"TTS Error: {str(e)}")
        print(f"Traceback: {error_details}")
        origin = request.headers.get("Origin", "")
        return jsonify({"error": str(e), "details": error_details}), 500, {
            "Access-Control-Allow-Origin": origin if validate_origin(request) else "null"
        }
