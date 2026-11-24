# 11. Choose reasoning per local model and raise Ollama's context window

Status: accepted, 2026-11-23.

## Context

Both local models are Qwen-family 4B models with optional thinking. Without thinking,
qwen3:4b refused every dev question. With thinking on, qwen3.5:4b's replies hit
`done_reason=length`. The cause was Ollama's default 4,096-token window, which silently
truncated the prompt and cut reasoning off before the JSON.

## Decision

- Reasoning is a per-model variant chosen on dev by the rule in
  [8](0008-pre-registered-selection-rules.md). The result is `qwen3:4b@think` and
  `qwen3.5:4b@nothink`. `OPENUSD_OLLAMA_REASONING` defaults to true.
- `num_ctx` is set to 16,384, enough for eight excerpts plus reasoning.

## Consequences

- qwen3:4b went from 0% to 85% of dev answerable questions answered with valid citations,
  at p50 13.1 s.
- qwen3.5:4b answers in 2.4 s but refuses more answerable questions (23% false refusals on
  dev, 33% on held-out).
- Evidence: `reports/variants_dev.md`.
