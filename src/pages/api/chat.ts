import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  const edgeUrl = import.meta.env.TERSONA_CHAT_URL || import.meta.env.PUBLIC_TERSONA_CHAT_URL;
  const edgeKey = import.meta.env.TERSONA_CHAT_KEY;

  if (!edgeUrl) {
    return json({ error: 'TERSONA_CHAT_URL is not configured' }, 500);
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid JSON' }, 400);
  }

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (edgeKey) {
    headers['x-tersona-chat-key'] = edgeKey;
  }

  const response = await fetch(edgeUrl, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  const text = await response.text();
  return new Response(text, {
    status: response.status,
    headers: {
      'Content-Type': response.headers.get('Content-Type') || 'application/json',
    },
  });
};

function json(body: object, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
