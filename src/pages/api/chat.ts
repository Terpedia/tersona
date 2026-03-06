import type { APIRoute } from 'astro';
import { GeminiService } from '../../lib/gemini';
import { getTerpeneById } from '../../data/terpenes';

export const POST: APIRoute = async ({ request }) => {
  try {
    const { terpeneId, message, history, apiKey } = await request.json();

    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'API key required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const terpene = getTerpeneById(terpeneId);
    if (!terpene) {
      return new Response(JSON.stringify({ error: 'Terpene not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const gemini = new GeminiService(apiKey);
    const response = await gemini.chat(terpene, message, history || []);

    return new Response(JSON.stringify({ response }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to process chat request' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
