# 12. Add a Gemini API adapter and price runs at official rates

Status: accepted, 2026-11-23.

## Context

The comparison includes a hosted model, Gemini 3.5 Flash-Lite, next to the local ones. It
must be selectable without code changes and keep its key out of the repository. Cost must be
comparable across runs, even though development used the free tier.

## Decision

- `OPENUSD_CHAT_PROVIDER=gemini` switches generation to the official `google-genai` SDK.
  Embeddings stay on Ollama, so retrieval is identical for every chat model.
- The key is a `SecretStr` read only from `.env`.
- Gemini 3.x takes `thinking_level`, not `thinking_budget`, so variants are written as
  `@level=X`.
- The SDK timeout is also the server-side deadline. Calls retry on 429, 500, 503 and 504.
- Cost per 100 questions uses the paid Standard prices in `eval/pricing.json`, with source and
  retrieval date. Thinking tokens are billed at the output rate. Ollama models are $0, and
  hardware and electricity are not counted.

## Consequences

- Flash-Lite costs about $0.15 per 100 dev questions and $0.12 per 100 held-out questions at
  list price. The runs themselves used the free tier.
- The free tier's per-day request caps limit how much can run in one day.
