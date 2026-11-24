# 1. Pin the corpus to one OpenUSD commit with SHA-256 digests

Status: accepted, 2026-11-23.

## Context

Answers cite exact source lines. If the upstream docs change, line numbers and expected
sources in the evaluation sets silently stop matching, and results stop being comparable.

## Decision

The corpus is every `docs/**/*.rst` file of OpenUSD v26.08 at commit
`ee47c679abde5b467a7b6a41f3b2285564a4222e`, listed in `corpus/manifest.json` with a SHA-256
digest per file. `LICENSE.txt` and `NOTICE.txt` from the same commit are required entries.
`build-manifest` regenerates the list from the GitHub tree; downloads refuse redirects, cap
file size at 2 MB and fail on any digest mismatch.

## Consequences

- Every chunk, citation and question source refers to one immutable text.
- Moving to a newer release is an explicit change: rebuild the manifest, re-check every
  question source (`check-questions`) and rerun all evaluations.
- Evidence: `reports/corpus.md` (76 documents, 70 with text, 952 chunks).
