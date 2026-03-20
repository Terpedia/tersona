"""
Cloud Function to proxy Vertex AI Gemini calls
Uses service account authentication (no API key needed)
"""
import functions_framework
from flask import Request, jsonify, make_response
import os
import json
from typing import List, Dict, Optional

# Google Cloud project and location
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "terpedia-489015")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# Initialize Vertex AI (uses service account from Cloud Function)
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
    aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_LOCATION)
    VERTEX_AI_AVAILABLE = True
except Exception as e:
    VERTEX_AI_AVAILABLE = False
    print(f"Warning: Vertex AI not available: {e}")

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
    
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 500
    
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
            
            # Call Vertex AI Gemini (uses service account auth automatically)
            model = GenerativeModel(
                model_name="gemini-2.0-flash-001",
                system_instruction=system_prompt
            )
            
            # Build conversation for Vertex AI format
            chat = model.start_chat(history=[])
            
            # Convert contents to Vertex AI format
            vertex_messages = []
            for msg in contents:
                if msg["role"] == "user":
                    vertex_messages.append(msg["parts"][0]["text"])
                elif msg["role"] == "model":
                    vertex_messages.append(msg["parts"][0]["text"])
            
            # Send message (Vertex AI handles conversation history)
            if len(vertex_messages) > 1:
                # Multi-turn conversation
                response = chat.send_message(vertex_messages[-1])
            else:
                # First message
                response = model.generate_content(vertex_messages[0] if vertex_messages else message)
            
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
