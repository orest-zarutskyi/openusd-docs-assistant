# 2. Chunk RST by structure while keeping exact line ranges

Status: accepted, 2026-11-23.

## Context

A citation is only checkable if each chunk maps back to a contiguous range of source lines.
Rendering RST to HTML would lose that mapping, and fixed-size windows cut glossary entries
and code samples in half.

## Decision

Chunks are cut from the raw RST text along headings and paragraphs, targeting about
2,300 characters, and each keeps its start and end line. Site plumbing (`raw`, `include`,
`contents`, `toctree`, `:orphan:`) is skipped; a `.. _label:` stays with the heading it
names; a code block stays with the paragraph that introduces it; a block more than three
times the target is split only at its base indentation.

## Consequences

- Every answer can link to `path#Lstart-Lend` on GitHub at the pinned commit.
- `docs/glossary.rst` becomes 129 small chunks, one or a few entries each, which suits
  definition questions.
- Some chunks stay large (up to 8,371 characters in `wp_ar2.rst`) to avoid splitting code.
- Evidence: `reports/corpus.md`.
