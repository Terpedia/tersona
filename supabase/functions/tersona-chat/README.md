# tersona-chat

Supabase Edge Function for server-side Tersona chat.

## Secrets

```bash
supabase secrets set GEMINI_API_KEY=...
supabase secrets set GEMINI_MODEL=gemini-2.0-flash
supabase secrets set TERPMED_RESULTS_URL=https://terpmed.terpedia.com/results.json
supabase secrets set TERSONA_CHAT_KEY=optional-shared-key
```

`TERSONA_CHAT_KEY` is optional. If set, clients must send `x-tersona-chat-key`.
`TERPMED_RESULTS_URL` is optional and defaults to `https://terpmed.terpedia.com/results.json`.

## Request

```json
{
  "tersonaId": "limonene",
  "message": "What do you bring to a daytime blend?",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "tersonaId": "limonene", "content": "Ciao!" }
  ]
}
```

Aliases accepted: `terpeneId`, `tersona`, `prompt`, `conversationHistory`, `activeTerpenes`.

When the user mentions a disease/effect term that appears in TerpMed, the function adds PubMed hit counts,
the source query URL, and top PMIDs to the model context. The response also includes `terpmed.matches` so the UI
can display citations.

## Deploy

```bash
supabase functions deploy tersona-chat
```
