import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  try {
    const { text, voiceConfig } = await request.json();
    
    // Get API key from environment or request
    const apiKey = import.meta.env.GOOGLE_CLOUD_API_KEY;
    
    if (!apiKey) {
      return new Response(
        JSON.stringify({ error: 'Google Cloud API key not configured' }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Call Google Cloud Text-to-Speech API
    const response = await fetch(
      `https://texttospeech.googleapis.com/v1/text:synthesize?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: { text },
          voice: {
            languageCode: voiceConfig.languageCode,
            name: voiceConfig.name,
            ssmlGender: voiceConfig.gender
          },
          audioConfig: {
            audioEncoding: 'MP3',
            pitch: 0,
            speakingRate: 1.0
          }
        })
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('TTS API error:', error);
      throw new Error('TTS request failed');
    }

    const data = await response.json();
    
    return new Response(JSON.stringify({ audioContent: data.audioContent }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('TTS API error:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to synthesize speech' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
