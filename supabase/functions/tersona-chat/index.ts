import {
  buildSystemPrompt,
  getTersona,
  listTersonas,
  renderConversation,
  type ChatMessage,
  type Tersona,
} from "../_shared/tersonas.ts";
import { buildTerpMedContext } from "../_shared/terpmed.ts";

type TersonaChatRequest = {
  message?: string;
  prompt?: string;
  tersonaId?: string;
  terpeneId?: string;
  tersona?: string;
  activeTersonas?: string[];
  activeTerpenes?: string[];
  history?: ChatMessage[];
  conversationHistory?: ChatMessage[];
  model?: string;
};

const cors: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-tersona-chat-key",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...cors },
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: cors });
  }

  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  const chatKey = Deno.env.get("TERSONA_CHAT_KEY");
  if (chatKey && req.headers.get("x-tersona-chat-key") !== chatKey) {
    return jsonResponse({ error: "Unauthorized" }, 401);
  }

  let body: TersonaChatRequest;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON" }, 400);
  }

  const message = typeof body.message === "string" ? body.message : body.prompt;
  if (!message || !message.trim()) {
    return jsonResponse({ error: "message is required" }, 400);
  }

  const activeIds = body.activeTersonas || body.activeTerpenes || [];
  const activeTersonas = activeIds.map((id) => getTersona(id)).filter((item) => Boolean(item)) as Tersona[];
  const explicitTersonaId = body.tersonaId || body.terpeneId || body.tersona;
  const tersona = explicitTersonaId
    ? getTersona(explicitTersonaId)
    : detectTersona(message, activeTersonas) || getTersona("terpenequeen");
  if (!tersona) {
    return jsonResponse(
      {
        error: "Tersona not found",
        availableTersonas: listTersonas().map(({ id, name }) => ({ id, name })),
      },
      404,
    );
  }

  const history = body.history || body.conversationHistory || [];

  const apiKey = Deno.env.get("GEMINI_API_KEY");
  if (!apiKey) {
    return jsonResponse({ error: "GEMINI_API_KEY is not configured" }, 500);
  }

  const model = body.model || Deno.env.get("GEMINI_MODEL") || "gemini-2.0-flash";
  let terpMedContext = "";
  let terpMedMatches: unknown[] = [];
  try {
    const terpMed = await buildTerpMedContext(message, tersona, { maxMatches: 3 });
    terpMedContext = terpMed.context;
    terpMedMatches = terpMed.matches;
  } catch (error) {
    console.warn("TerpMed context unavailable:", error);
  }
  const systemPrompt = buildSystemPrompt(tersona, activeTersonas) + terpMedContext;
  const prompt = renderConversation(history, message);

  const geminiResponse = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: {
          parts: [{ text: systemPrompt }],
        },
        contents: [
          {
            role: "user",
            parts: [{ text: prompt }],
          },
        ],
        generationConfig: {
          temperature: 0.8,
          maxOutputTokens: 700,
        },
      }),
    },
  );

  if (!geminiResponse.ok) {
    const details = await geminiResponse.text();
    return jsonResponse({ error: "Gemini request failed", status: geminiResponse.status, details }, 502);
  }

  const data = await geminiResponse.json();
  const response = data?.candidates?.[0]?.content?.parts
    ?.map((part: { text?: string }) => part.text || "")
    .join("")
    .trim();

  if (!response) {
    return jsonResponse({ error: "Gemini returned an empty response", raw: data }, 502);
  }

  return jsonResponse({
    response,
    tersona: {
      id: tersona.id,
      name: tersona.name,
      emoji: tersona.emoji,
      voice: tersona.voice,
      greeting: tersona.greeting,
    },
    model,
    terpmed: {
      matches: terpMedMatches,
    },
    usage: data?.usageMetadata || null,
  });
});

function detectTersona(message: string, activeTersonas: Tersona[]) {
  const lower = message.toLowerCase();
  const candidates = activeTersonas.length ? activeTersonas : listTersonas();
  return candidates.find((candidate) => {
    return lower.includes(candidate.id.toLowerCase()) || lower.includes(candidate.name.toLowerCase());
  });
}
