"""
Cloud Run service for Terpene Chat - Vertex AI + STT/TTS
Uses service account authentication (no API key needed)
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
import json
import re
import time

# Google Cloud project and location
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "terpedia-489015")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# Lazy initialization flags
VERTEX_AI_INITIALIZED = False
VERTEX_AI_AVAILABLE = True
SPEECH_AVAILABLE = True

# Throttle expensive LLM ping in /warm (many tabs / refreshes)
_last_llm_warm_ts: float = 0.0
LLM_WARM_MIN_INTERVAL_SEC = float(os.getenv("LLM_WARM_MIN_INTERVAL_SEC", "90"))

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

def get_generative_model():
    try:
        from vertexai.generative_models import GenerativeModel
        return GenerativeModel
    except ImportError:
        from vertexai.preview.generative_models import GenerativeModel
        return GenerativeModel


def _text_part(text: str):
    from vertexai.generative_models import Part

    if hasattr(Part, "from_text"):
        return Part.from_text(text)
    return Part(text=text)


def build_vertex_chat_history(conversation_history: List[Dict]) -> List:
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


def strip_markdown(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^\*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\1", text, flags=re.MULTILINE)
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


def strip_fantasized_guest_dialogue_from_host(text: str) -> str:
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


def detect_invited_terpenes(
    terpenequeen_response: str,
    active_terpenes: List[str],
    panel_terpene_ids: Optional[List[str]] = None,
) -> List[str]:
    if not terpenequeen_response or not isinstance(terpenequeen_response, str):
        return []
    if not active_terpenes:
        return []
    response_lower = terpenequeen_response.lower()
    invited = []
    has_question = "?" in terpenequeen_response or any(
        word in response_lower
        for word in [
            "what do you",
            "how do you",
            "tell me",
            "can you",
            "would you",
            "what does",
            "how does",
            "tell us",
            "share",
            "think about",
            "invite",
            "ask",
            "hear from",
            "thoughts",
            "perspective",
            "take",
            "are you",
            "could you",
        ]
    )
    is_invitation = any(
        phrase in response_lower
        for phrase in [
            "let me ask",
            "i'd like to ask",
            "i want to hear",
            "let's ask",
            "let's hear",
            "invite",
            "bring in",
            "get",
            "call on",
            "i'd love to hear",
            "love to hear",
            "would have",
            "would be great",
            "insights",
            "perspective",
        ]
    )
    has_terpene_mention = False
    for terpene_id in active_terpenes:
        if terpene_id != "terpenequeen" and terpene_id.lower() in response_lower:
            has_terpene_mention = True
            break
    if not has_question and not is_invitation and not has_terpene_mention:
        return []
    terpene_aliases = {
        "limonene": ["limonene", "lemon", "citrus"],
        "myrcene": ["myrcene"],
        "pinene": ["pinene", "alpha-pinene", "pine", "alpha pinene"],
        "linalool": ["linalool", "lavender", "linallok", "linalol"],
        "caryophyllene": ["caryophyllene", "beta-caryophyllene", "pepper", "clove", "beta caryophyllene"],
        "humulene": ["humulene", "hop"],
        "terpinolene": ["terpinolene"],
        "ocimene": ["ocimene", "basil"],
        "bisabolol": ["bisabolol", "chamomile"],
        "geraniol": ["geraniol", "rose", "geranium"],
    }
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
    allow_ids = [t for t in active_terpenes if t and t.lower() != "terpenequeen"]
    for terpene_id in allow_ids:
        for token in [terpene_id.lower(), *terpene_aliases.get(terpene_id, [])]:
            if len(token) < 3:
                continue
            if re.search(rf"(?:^|[\s\.\!\*]){re.escape(token)}\s*,", response_lower):
                invited.append(terpene_id)
                break
    question_cues = ("?", "what", "how", "tell", "ask", "invite", "are you", "can you", "could you")
    for terpene_id in active_terpenes:
        if terpene_id == "terpenequeen":
            continue
        if terpene_id.lower() in response_lower:
            terpene_pos = response_lower.find(terpene_id.lower())
            rest_after = response_lower[terpene_pos:]
            nearby_text = response_lower[max(0, terpene_pos - 80) : terpene_pos + 220]
            if any(word in nearby_text for word in question_cues) or "?" in rest_after:
                invited.append(terpene_id)
                continue
        aliases = terpene_aliases.get(terpene_id, [])
        for alias in aliases:
            if len(alias) < 3 or alias not in response_lower:
                continue
            alias_pos = response_lower.find(alias)
            rest_after = response_lower[alias_pos:]
            nearby_text = response_lower[max(0, alias_pos - 80) : alias_pos + 220]
            if any(word in nearby_text for word in question_cues) or "?" in rest_after:
                invited.append(terpene_id)
                break
    seen = set()
    ordered: List[str] = []

    def _first_mention_pos(tid: str) -> int:
        p = response_lower.find(tid.lower())
        if p >= 0:
            return p
        for a in terpene_aliases.get(tid, []):
            if len(a) >= 3:
                ap = response_lower.find(a)
                if ap >= 0:
                    return ap
        return 10**9

    for tid in sorted(set(invited), key=_first_mention_pos):
        if tid == "terpenequeen":
            continue
        if tid not in seen:
            seen.add(tid)
            ordered.append(tid)
    if panel_terpene_ids:
        allow = {t for t in panel_terpene_ids if t and t.lower() != "terpenequeen"}
        ordered = [tid for tid in ordered if tid in allow]
    return ordered


# Terpene system prompts (simplified - full version in terpenes.py)
TERPENE_PROMPTS = {
    "terpenequeen": """You are TerpeneQueen, the interviewer persona of Susan Trapp, PhD. Expert in terpenes, cannabis botany, and natural products. Warm, curious, and professional. When guest terpenes are on the panel, do not give detailed science on their behalf—invite them by name to answer; explain mechanisms in depth only when you are the sole speaker. Stay topical: answer what the user asked first; avoid unrelated tangents and "while we're here" threads unless they asked for them.

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

def _panel_guests(active_terpenes: List[str]) -> List[str]:
    return [t for t in active_terpenes if t and t.lower() != "terpenequeen"]


def _last_assistant_terpene_id(conversation_history: List[Dict]) -> Optional[str]:
    for msg in reversed(conversation_history or []):
        if msg.get("role") == "assistant":
            tid = msg.get("terpene_id")
            if tid:
                return tid
    return None


def _prev_assistant_terpene_id(conversation_history: List[Dict]) -> Optional[str]:
    """The assistant turn before the most recent assistant (for panel routing)."""
    seen_last = False
    for msg in reversed(conversation_history or []):
        if msg.get("role") != "assistant":
            continue
        tid = msg.get("terpene_id")
        if not tid:
            continue
        if not seen_last:
            seen_last = True
            continue
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
    try:
        from terpenes import get_terpene
        for tid in guests:
            name = get_terpene(tid)["name"].lower()
            if len(name) > 3 and name in message_lower:
                return tid
    except Exception:
        pass
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
    """Detect which terpenes are mentioned or should respond (panel routing when TerpeneQueen + guests)."""
    conversation_history = conversation_history or []
    message_lower = message.lower()
    mentioned = []

    terpene_aliases = {
        "terpenequeen": ["terpenequeen", "susan", "susan trapp", "terpene queen"],
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
        if any(word in message_lower for word in ["all", "everyone", "panel", "you all", "what do you"]):
            return active_terpenes
        if len(active_terpenes) == 1:
            return active_terpenes

        guests = _panel_guests(active_terpenes)
        has_tq = any(t.lower() == "terpenequeen" for t in active_terpenes)

        if not guests:
            return [active_terpenes[0]]

        if has_tq and len(guests) >= 1:
            # First API request: let TerpeneQueen host so she can invite guests in one round.
            # Otherwise keywords like "focus" route straight to Pinene and the panel "stops" there.
            if not conversation_history:
                return ["terpenequeen"]
            last = _last_assistant_terpene_id(conversation_history)
            if last and last != "terpenequeen" and last in guests:
                return ["terpenequeen"]
            science_cues = (
                "the science", "science behind", "about science", "scientific",
                "mechanism", "receptors", "receptor", "pathway", "biochemistry",
                "neurotransmitter", "gaba", "cb1", "cb2", "endocannabinoid",
                "how does it work", "how do they work", "at the molecular", "evidence for",
            )
            if last == "terpenequeen":
                prev_tid = _prev_assistant_terpene_id(conversation_history)
                # Guest spoke, then host "closing beat" — user is usually replying to Susan, not the guest.
                if prev_tid and prev_tid in guests:
                    return ["terpenequeen"]
                hit = _topic_match_guest(message_lower, guests)
                if hit:
                    return [hit]
                if any(cue in message_lower for cue in science_cues):
                    nxt = _pick_guest_round_robin(active_terpenes, conversation_history)
                    if nxt:
                        return [nxt]
                nxt = _pick_guest_round_robin(active_terpenes, conversation_history)
                return [nxt] if nxt else [guests[0]]
            rr = _pick_guest_round_robin(active_terpenes, conversation_history)
            return [rr] if rr else [guests[0]]

        return [active_terpenes[0]]

    return list(set(mentioned))


def _vertex_response_text(response) -> Optional[str]:
    if not response:
        return None
    text = response.text if hasattr(response, "text") else None
    if text:
        return text
    if hasattr(response, "candidates") and response.candidates:
        cand = response.candidates[0]
        if hasattr(cand, "content") and hasattr(cand.content, "parts") and cand.content.parts:
            return cand.content.parts[0].text
    return None


def _autoplay_next_speaker(updated_history: List[Dict], guests: List[str]) -> Optional[str]:
    if not guests:
        return None
    last = _last_assistant_terpene_id(updated_history)
    if last is None or last == "terpenequeen":
        n = sum(
            1
            for m in updated_history
            if m.get("role") == "assistant" and m.get("terpene_id") in guests
        )
        return guests[n % len(guests)]
    if last in guests:
        return "terpenequeen"
    return "terpenequeen"


def run_panel_autoplay(
    GenerativeModel,
    active_terpenes: List[str],
    updated_history: List[Dict],
    responses: List[Dict[str, str]],
    autoplay_minutes: float,
) -> None:
    """Append alternating host/guest turns until time budget (mutates history and responses)."""
    guests = _panel_guests(active_terpenes)
    has_tq = any(t.lower() == "terpenequeen" for t in active_terpenes)
    if not guests or not has_tq or autoplay_minutes <= 0:
        return
    deadline = time.monotonic() + autoplay_minutes * 60.0
    t0 = time.monotonic()
    max_turns = 240
    turn_msg_guest = (
        "[Panel autoplay — your turn only. One short contribution; do not write dialogue for other terpenes.]"
    )
    tq_session_ctx_added = False
    autoplay_suffix = (
        "\n\nPANEL AUTOPLAY: The human is listening; they are not typing between lines. "
        "Do not ask them to type a reply in chat. Another speaker follows. "
        "Pace like **spoken conversation** between people in a room—usually **1–3 short paragraphs worth** of speech, "
        "not a dense essay or a rapid list. Plain text only."
    )
    turns = 0
    while time.monotonic() < deadline and turns < max_turns:
        next_id = _autoplay_next_speaker(updated_history, guests)
        if not next_id:
            break
        try:
            from terpenes import get_terpene

            tp = get_terpene(next_id)
            sp = tp.get("system_prompt", TERPENE_PROMPTS.get(next_id, TERPENE_PROMPTS["terpenequeen"]))
        except ImportError:
            sp = TERPENE_PROMPTS.get(next_id, TERPENE_PROMPTS["terpenequeen"])
        sp += autoplay_suffix
        if next_id == "terpenequeen":
            sp += (
                " Continue as host: brief reaction, optional comparison, invite a guest by name—"
                "do not answer for them. **Guide** the segment at a **human** pace—plan the next beat without rushing."
            )
            try:
                from terpenes import (
                    build_host_autoplay_phase_hint,
                    build_host_panel_context,
                    build_host_session_time_context,
                )

                if not tq_session_ctx_added:
                    stc = build_host_session_time_context(autoplay_minutes)
                    if stc:
                        sp += "\n\n" + stc
                    tq_session_ctx_added = True
                elapsed = time.monotonic() - t0
                sp += "\n\n" + build_host_autoplay_phase_hint(elapsed, autoplay_minutes)
                pc = build_host_panel_context(active_terpenes)
                if pc:
                    sp += "\n\n" + pc
            except ImportError:
                pass
        else:
            sp += " Continue in character from the thread; one voice only."
        if len(active_terpenes) > 1 and next_id != "terpenequeen":
            sp += (
                "\n\nOVERRIDE: Ignore any instruction to ask the human user to reply in this turn—they are only listening. "
                "Still keep delivery **conversational and unhurried**."
            )
        if "plain text" not in sp.lower():
            sp += "\n\nIMPORTANT: Plain text only, no markdown."

        model = GenerativeModel(
            model_name="gemini-2.0-flash-001",
            system_instruction=sp,
        )
        hist = build_vertex_chat_history(updated_history)
        turn_user = (
            "[Autoplay — host turn: steer the segment per your run-of-show; one contribution only.]"
            if next_id == "terpenequeen"
            else turn_msg_guest
        )
        try:
            if hist:
                ch = model.start_chat(history=hist)
                resp = ch.send_message(turn_user)
            else:
                resp = model.generate_content(turn_user)
            txt = _vertex_response_text(resp)
            if not txt:
                break
            txt = strip_markdown(txt)
            responses.append({"terpene_id": next_id, "response": txt})
            updated_history.append({"role": "assistant", "content": txt, "terpene_id": next_id})
            turns += 1
        except Exception as e:
            print(f"DEBUG: panel autoplay stopped: {e}")
            break


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    active_terpenes: Optional[List[str]] = ["terpenequeen"]
    conversation_history: Optional[List[Dict[str, str]]] = []
    autoplay_panel_minutes: float = Field(
        0.0,
        ge=0.0,
        le=15.0,
        description="If >0, host+guests keep speaking for about this many minutes (max 15).",
    )

class ChatResponse(BaseModel):
    responses: List[Dict[str, str]]
    conversation_history: List[Dict[str, str]]


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "terpene-api"}


@app.get("/warm")
async def warm():
    """
    Wake Cloud Run, initialize Vertex, and optionally run a tiny LLM call so the first
    real /chat is faster. Safe to call from the browser on page load (idempotent).
    """
    global _last_llm_warm_ts
    t0 = time.time()
    init_vertex_ai()
    out = {
        "status": "ok",
        "service": "terpene-api",
        "vertex_initialized": VERTEX_AI_INITIALIZED and VERTEX_AI_AVAILABLE,
        "llm_ping": False,
    }
    if not VERTEX_AI_AVAILABLE:
        out["note"] = "Vertex AI unavailable; container only warmed"
        out["elapsed_ms"] = int((time.time() - t0) * 1000)
        return out

    now = time.time()
    if now - _last_llm_warm_ts < LLM_WARM_MIN_INTERVAL_SEC:
        out["llm_ping_skipped"] = True
        out["llm_ping_skip_sec"] = round(LLM_WARM_MIN_INTERVAL_SEC - (now - _last_llm_warm_ts), 1)
        out["elapsed_ms"] = int((time.time() - t0) * 1000)
        return out

    try:
        GenerativeModel = get_generative_model()
        try:
            from vertexai.generative_models import GenerationConfig

            gen_cfg = GenerationConfig(max_output_tokens=8, candidate_count=1, temperature=0)
        except Exception:
            gen_cfg = None

        model = GenerativeModel(
            model_name="gemini-2.0-flash-001",
            system_instruction="Reply with exactly the single word: OK",
        )
        if gen_cfg is not None:
            model.generate_content(".", generation_config=gen_cfg)
        else:
            model.generate_content(".")
        _last_llm_warm_ts = time.time()
        out["llm_ping"] = True
    except Exception as e:
        out["llm_ping_error"] = str(e)[:200]
    out["elapsed_ms"] = int((time.time() - t0) * 1000)
    return out


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    POST /chat
    Body: message, active_terpenes, conversation_history,
    optional autoplay_panel_minutes (0–15): host+guests keep taking turns for ~that many minutes.
    """
    init_vertex_ai()
    if not VERTEX_AI_AVAILABLE:
        raise HTTPException(status_code=500, detail="Vertex AI not available")

    try:
        GenerativeModel = get_generative_model()
        message = request.message
        active_terpenes = request.active_terpenes or ["terpenequeen"]
        conversation_history = request.conversation_history or []
        ap_min = float(request.autoplay_panel_minutes or 0.0)
        ap_min = max(0.0, min(ap_min, 15.0))

        responding_terpenes = detect_mentioned_terpenes(message, active_terpenes, conversation_history)

        responses = []
        updated_history = list(conversation_history)
        updated_history.append({"role": "user", "content": message})

        for terpene_id in responding_terpenes:
            try:
                from terpenes import get_terpene

                terpene = get_terpene(terpene_id)
                system_prompt = terpene.get(
                    "system_prompt", TERPENE_PROMPTS.get(terpene_id, TERPENE_PROMPTS["terpenequeen"])
                )
            except ImportError:
                system_prompt = TERPENE_PROMPTS.get(terpene_id, TERPENE_PROMPTS["terpenequeen"])

            if len(active_terpenes) > 1:
                other_names = [t for t in active_terpenes if t != terpene_id]
                system_prompt += f"\n\nCONTEXT: You are in a panel discussion with: {', '.join(other_names)}. Respond when directly addressed. Keep responses concise."
                system_prompt += "\n\nOUTPUT: In this message, speak ONLY as your own persona. Do not write dialogue, speeches, or replies for other terpenes—they have separate messages."
                system_prompt += (
                    "\n\nHUMAN PACE: This should feel like **people talking**, not a rapid Q&A machine—"
                    "natural rhythm, one main beat per turn unless the topic truly needs more."
                )
                if terpene_id != "terpenequeen":
                    system_prompt += (
                        "\n\nLISTENER: If it fits naturally, close with a light nod toward the human; "
                        "you do not need to force a question every turn."
                    )

            if terpene_id == "terpenequeen":
                try:
                    from terpenes import build_host_panel_context, build_host_session_time_context

                    panel_ctx = build_host_panel_context(active_terpenes)
                    if panel_ctx:
                        system_prompt += "\n\n" + panel_ctx
                    if ap_min > 0:
                        stc = build_host_session_time_context(ap_min)
                        if stc:
                            system_prompt += "\n\n" + stc
                except ImportError:
                    pass

            if "plain text" not in system_prompt.lower() and "markdown" not in system_prompt.lower():
                system_prompt += "\n\nIMPORTANT: Respond in plain text only - no markdown formatting (no **bold**, *italic*, # headers, `code`, [links](url), etc.). Write naturally as if speaking in a conversation."

            model = GenerativeModel(
                model_name="gemini-2.0-flash-001",
                system_instruction=system_prompt,
            )
            history = build_vertex_chat_history(conversation_history)

            try:
                if history:
                    chat_session = model.start_chat(history=history)
                    response = chat_session.send_message(message)
                else:
                    response = model.generate_content(message)

                if not response:
                    raise ValueError("No response object returned from model")
                assistant_text = response.text if hasattr(response, "text") else None
                if not assistant_text and hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                        assistant_text = candidate.content.parts[0].text if candidate.content.parts else None
                if not assistant_text:
                    raise ValueError("Response text is empty or unavailable")
            except Exception as gen_error:
                error_msg = str(gen_error)
                print(f"DEBUG: Error generating response for {terpene_id}: {error_msg}")
                assistant_text = (
                    f"I apologize, but I encountered an error while generating a response: {error_msg}. Please try again."
                )

            if not assistant_text:
                assistant_text = "I'm sorry, I didn't get a response. Could you try again?"

            assistant_text_md = strip_markdown(assistant_text)
            tq_for_invite = assistant_text_md
            if terpene_id == "terpenequeen" and len(_panel_guests(active_terpenes)) >= 1:
                assistant_text = strip_fantasized_guest_dialogue_from_host(assistant_text_md)
            else:
                assistant_text = assistant_text_md

            responses.append({"terpene_id": terpene_id, "response": assistant_text})
            updated_history.append(
                {"role": "assistant", "content": assistant_text, "terpene_id": terpene_id}
            )

            if terpene_id == "terpenequeen":
                try:
                    try:
                        from terpenes import list_terpenes

                        all_terpene_ids = [t["id"] for t in list_terpenes()]
                    except ImportError:
                        all_terpene_ids = active_terpenes

                    invited_terpenes = detect_invited_terpenes(
                        tq_for_invite, all_terpene_ids, panel_terpene_ids=active_terpenes
                    )
                    if invited_terpenes:
                        for invited_id in invited_terpenes:
                            print(f"DEBUG: invite {invited_id}")
                            if invited_id in [r["terpene_id"] for r in responses]:
                                continue
                            try:
                                from terpenes import get_terpene

                                invited_terpene = get_terpene(invited_id)
                                invited_system_prompt = invited_terpene.get(
                                    "system_prompt",
                                    TERPENE_PROMPTS.get(invited_id, TERPENE_PROMPTS["terpenequeen"]),
                                )
                            except ImportError:
                                invited_system_prompt = TERPENE_PROMPTS.get(
                                    invited_id, TERPENE_PROMPTS["terpenequeen"]
                                )

                            invited_system_prompt += f'\n\nCONTEXT: TerpeneQueen (Susan Trapp, PhD) just asked you a question: "{tq_for_invite}" Please respond to her question naturally and in character.'
                            invited_system_prompt += (
                                "\n\nPACE: Relaxed **human** rhythm—let your point land before you tack on extras.\n"
                                "LISTENER: Optionally invite the human with a warm line or question; "
                                "it doesn't have to be every message."
                            )
                            if "plain text" not in invited_system_prompt.lower() and "markdown" not in invited_system_prompt.lower():
                                invited_system_prompt += "\n\nIMPORTANT: Respond in plain text only - no markdown formatting (no **bold**, *italic*, # headers, `code`, [links](url), etc.). Write naturally as if speaking in a conversation."

                            invited_history = build_vertex_chat_history(updated_history)
                            invited_model = GenerativeModel(
                                model_name="gemini-2.0-flash-001",
                                system_instruction=invited_system_prompt,
                            )
                            invitation_prompt = f'TerpeneQueen (Susan Trapp, PhD) just asked you: "{tq_for_invite}"\n\nPlease respond to her question naturally and in character.'
                            try:
                                if invited_history:
                                    inv_chat = invited_model.start_chat(history=invited_history)
                                    inv_resp = inv_chat.send_message(invitation_prompt)
                                else:
                                    inv_resp = invited_model.generate_content(invitation_prompt)
                                if not inv_resp:
                                    raise ValueError("No response object returned from model")
                                invited_text = inv_resp.text if hasattr(inv_resp, "text") else None
                                if not invited_text and hasattr(inv_resp, "candidates") and inv_resp.candidates:
                                    c = inv_resp.candidates[0]
                                    if hasattr(c, "content") and hasattr(c.content, "parts"):
                                        invited_text = c.content.parts[0].text if c.content.parts else None
                                if not invited_text:
                                    raise ValueError("Response text is empty or unavailable")
                                invited_text = strip_markdown(invited_text)
                                responses.append({"terpene_id": invited_id, "response": invited_text})
                                updated_history.append(
                                    {
                                        "role": "assistant",
                                        "content": invited_text,
                                        "terpene_id": invited_id,
                                    }
                                )
                            except Exception as inv_err:
                                err_msg = str(inv_err)
                                print(f"DEBUG: invited guest {invited_id} error: {err_msg}")
                                err_resp = f"I apologize, but I encountered an error while generating a response: {err_msg}. Please try again."
                                responses.append({"terpene_id": invited_id, "response": err_resp})
                                updated_history.append(
                                    {
                                        "role": "assistant",
                                        "content": err_resp,
                                        "terpene_id": invited_id,
                                    }
                                )

                        # Host closing: after guest(s) spoke, one beat toward the human (skip if autoplay will continue)
                        panel_guest_ids = set(_panel_guests(active_terpenes))
                        if (
                            ap_min <= 0
                            and panel_guest_ids
                            and any(r.get("terpene_id") in panel_guest_ids for r in responses)
                        ):
                            try:
                                from terpenes import get_terpene as _gtq_closing

                                tq_base = _gtq_closing("terpenequeen").get(
                                    "system_prompt", TERPENE_PROMPTS["terpenequeen"]
                                )
                            except ImportError:
                                tq_base = TERPENE_PROMPTS["terpenequeen"]
                            closing_si = (
                                tq_base
                                + "\n\nTHIS MESSAGE ONLY — CLOSING BEAT: Guest terpenes have already replied above. "
                                "Do not invite another terpene. In 2–4 sentences, briefly acknowledge what was shared, "
                                "then invite the **human listener** with one natural, welcoming question or open door—"
                                "like ending a real conversation, not a survey. "
                                "Optionally one short line on how you might continue **when** they answer. "
                                "Plain text only."
                            )
                            if "plain text" not in closing_si.lower():
                                closing_si += "\n\nIMPORTANT: Plain text only, no markdown."
                            closing_model = GenerativeModel(
                                model_name="gemini-2.0-flash-001",
                                system_instruction=closing_si,
                            )
                            closing_hist = build_vertex_chat_history(updated_history)
                            closing_msg = (
                                "[Host closing for this round] Wrap this beat the way you would in person—"
                                "warm, unhurried, one clear thread for them to pick up if they want."
                            )
                            try:
                                if closing_hist:
                                    c_chat = closing_model.start_chat(history=closing_hist)
                                    c_resp = c_chat.send_message(closing_msg)
                                else:
                                    c_resp = closing_model.generate_content(closing_msg)
                                c_text = c_resp.text if c_resp and hasattr(c_resp, "text") else None
                                if not c_text and c_resp and hasattr(c_resp, "candidates") and c_resp.candidates:
                                    cand = c_resp.candidates[0]
                                    if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                                        c_text = cand.content.parts[0].text if cand.content.parts else None
                                if c_text:
                                    c_text = strip_markdown(c_text)
                                    responses.append({"terpene_id": "terpenequeen", "response": c_text})
                                    updated_history.append(
                                        {
                                            "role": "assistant",
                                            "content": c_text,
                                            "terpene_id": "terpenequeen",
                                        }
                                    )
                            except Exception as close_err:
                                print(f"DEBUG: host closing beat: {close_err}")
                except Exception as invite_outer:
                    print(f"DEBUG: invitation block: {invite_outer}")

        if ap_min > 0:
            run_panel_autoplay(
                GenerativeModel,
                active_terpenes,
                updated_history,
                responses,
                ap_min,
            )

        return ChatResponse(responses=responses, conversation_history=updated_history)

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
        fname = file.filename or "recording.webm"

        from google.cloud import speech_v1
        from stt_helpers import prepare_audio_and_config

        audio_content, config = prepare_audio_and_config(
            audio_content, fname, language or "en-US"
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
        # Surface enough detail in logs; Google STT InvalidArgument is often just "MP3" / "FLAC".
        import traceback

        traceback.print_exc()
        detail = str(e).strip() or repr(e)
        cleaned = detail.strip().strip('"').strip("'")
        if cleaned in ("MP3", "FLAC", "LINEAR16"):
            detail = (
                "Speech-to-Text rejected the audio (encoding or sample rate mismatch). "
                "Try again, or use Chrome/Edge (WebM/Opus recording)."
            )
        raise HTTPException(status_code=500, detail=detail[:2000])


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
        from google.cloud import texttospeech_v1
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
