# MSR Event Hub – Chat Web App

A modern chat UI using React, Vite, Fluent UI v9, and Azure OpenAI.

## Quick start

1. Copy `.env.example` to `.env`. By default the app calls the hub backend at `VITE_CHAT_API_BASE` (managed identity). For bridge/Showcase-based prod, point `VITE_CHAT_API_BASE` to that gateway.
2. From `web/chat`: `npm install`
3. Run dev server: `npm run dev`
4. Build for production: `npm run build`

## Azure OpenAI

- Uses the Chat Completions API with `stream=true`.
- Preferred: proxy through the hub backend (uses managed identity). Configure `VITE_CHAT_API_BASE` (default `/api`).
- Optional local fallback: direct Azure OpenAI with `VITE_AOAI_ENDPOINT`, `VITE_AOAI_DEPLOYMENT`, `VITE_AOAI_API_VERSION`, `VITE_AOAI_KEY`.
- For production, do not ship keys in the client; rely on the backend/managed identity path.

## Notes

- Output lives in `dist/` (configured via Vite). Adjust pipeline to publish or serve from the hub backend.
- Styling uses Fluent UI components plus a light gradient background in `src/styles.css`.
