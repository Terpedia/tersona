import { GoogleGenerativeAI } from '@google/generative-ai';
import type { TerpenePersona } from '../data/terpenes';

export class GeminiService {
  private genAI: GoogleGenerativeAI;
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
    this.genAI = new GoogleGenerativeAI(apiKey);
  }

  /**
   * Generate a conversational response from the terpene persona
   */
  async chat(
    terpene: TerpenePersona,
    userMessage: string,
    conversationHistory: Array<{ role: string; content: string }> = []
  ): Promise<string> {
    const model = this.genAI.getGenerativeModel({ model: 'gemini-pro' });

    const systemPrompt = `You are ${terpene.name}, a terpene molecule with a distinct personality.

PERSONALITY: ${terpene.personality}

YOUR TRAITS: ${terpene.traits.join(', ')}

YOUR BIOACTIVITY: You have these therapeutic properties: ${terpene.bioactivity.join(', ')}

YOUR BACKGROUND: You come from ${terpene.region} and embody the essence of that place.

YOUR CHEMICAL NATURE: ${terpene.chemicalFormula}

CONVERSATION STYLE:
- Stay in character as ${terpene.name}
- Reference your region, traits, and bioactivity naturally in conversation
- Be helpful and informative about terpenes and their properties
- Maintain your unique personality in every response
- Use occasional phrases that reflect your regional origin
- Keep responses conversational and engaging (2-4 sentences typically)
- You can discuss your molecular structure, where you're found in nature, and how you interact with the human body

IMPORTANT: Never break character. You ARE ${terpene.name}, not an AI pretending to be one.`;

    const history = conversationHistory
      .map(msg => `${msg.role === 'user' ? 'Human' : terpene.name}: ${msg.content}`)
      .join('\n\n');

    const prompt = `${systemPrompt}\n\n${history ? 'CONVERSATION SO FAR:\n' + history + '\n\n' : ''}Human: ${userMessage}\n\n${terpene.name}:`;

    try {
      const result = await model.generateContent(prompt);
      const response = await result.response;
      return response.text();
    } catch (error) {
      console.error('Gemini chat error:', error);
      throw new Error('Failed to generate response');
    }
  }

  /**
   * Convert text to speech using Google Cloud TTS
   * Note: This requires Google Cloud TTS API, not Gemini
   * Returns audio as base64-encoded string
   */
  async textToSpeech(
    text: string,
    voiceConfig: TerpenePersona['voiceConfig']
  ): Promise<string> {
    // This endpoint needs to be proxied through your API route
    // for security (to hide API keys)
    const response = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voiceConfig })
    });

    if (!response.ok) {
      throw new Error('TTS request failed');
    }

    const data = await response.json();
    return data.audioContent;
  }

  /**
   * Convert speech to text using Google Cloud STT
   * Note: This requires Google Cloud Speech-to-Text API
   */
  async speechToText(audioBlob: Blob): Promise<string> {
    // This endpoint needs to be proxied through your API route
    const formData = new FormData();
    formData.append('audio', audioBlob);

    const response = await fetch('/api/stt', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('STT request failed');
    }

    const data = await response.json();
    return data.transcript;
  }
}

// Client-side helper for browser
export class BrowserGeminiClient {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async chat(
    terpene: TerpenePersona,
    userMessage: string,
    conversationHistory: Array<{ role: string; content: string }> = []
  ): Promise<string> {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        terpeneId: terpene.id,
        message: userMessage,
        history: conversationHistory,
        apiKey: this.apiKey
      })
    });

    if (!response.ok) {
      throw new Error('Chat request failed');
    }

    const data = await response.json();
    return data.response;
  }
}
