# 9. Accept a citation only if its quote appears in the chunk, ignoring RST markup

Status: accepted, 2026-11-23.

## Context

The API returns evidence quotes and links them to source lines, so a quote that is not in the
cited chunk is a fabricated citation. Models, however, quote the rendered meaning of RST:
they drop `**`, backticks and role syntax such as `:usda:` and reflow lines.

## Decision

`quotes.normalize_rst` strips inline markup, roles and link targets and collapses whitespace
on both sides before comparing. The comparison stays word-exact: no fuzzy matching, and
only a trailing or leading ellipsis is trimmed. An answer counts only if every one of its
quotes passes; otherwise the outcome is `invalid_citation`.

## Consequences

- Markup differences no longer fail honest quotes, while paraphrased or invented quotes still do.
- Citation validity is reported per answer and quote validity per quote.
- A model that quotes correctly but loosely is still penalised. This shows up as most of the
  gap between "answered" and "answered with valid citations" in `reports/variants_dev.md`.
