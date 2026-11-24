# 10. Require status, answer and evidence in the model's JSON output

Status: accepted, 2026-11-23.

## Context

The answer is produced as structured output (JSON schema in Ollama, `response_json_schema` in
Gemini). With optional fields, qwen3.5:4b returned `status: answer` with an empty answer, and
the run counted it as answered.

## Decision

`answer_schema()` marks `status`, `answer` and `evidence` as required. A reply that fails to
parse or validate becomes `invalid_output`, with its token usage still recorded. Output is
capped at 800 tokens, or 6,144 when reasoning is on, because thinking tokens count against
the same limit.

## Consequences

- An empty or half-formed answer can no longer pass as an answer.
- Invalid output is a separate outcome in every report (0% for all three chosen variants on
  dev and held-out).
