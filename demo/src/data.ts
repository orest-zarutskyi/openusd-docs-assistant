// Everything shown in the video comes from a real run; nothing here is invented.
// - Answers, sources and the refusal: POST /ask on 2026-11-24 (docs/demo.md), qwen3:4b with
//   thinking, hybrid + bge-reranker-base retrieval, top_k 8. Quotes are shown with RST markup
//   (roles, backticks) removed; "…" marks a cut.
// - Reranker scores: the deployed reranker's top score for each question, computed with the
//   shipped settings; the gate is OPENUSD_RERANK_MIN_SCORE (-0.9831), fitted on dev.
// - Metrics: reports/retrieval_heldout.md, reports/answers_*.md, reports/judge_calibration_dev.md.

export const GATE = -0.9831;

export const ANSWERED = {
  question: "Which composition arc lets me open a stage before loading a heavy asset?",
  rerankScore: 0.2508,
  answer: "Payload",
  sources: [
    {
      path: "docs/maxperf.rst",
      lines: "L114–L143",
      title: "Package assets with payloads",
      quote:
        "USD provides a composition arc called a Payload that is essentially a “deferred reference”.",
    },
    {
      path: "docs/glossary.rst",
      lines: "L2211–L2239",
      title: "Payload",
      quote:
        "When a Stage is opened with UsdStage::InitialLoadSet::LoadNone specified, Payload arcs are recorded, but not traversed.",
    },
    {
      path: "docs/intro.rst",
      lines: "L164–L191",
      title: "USD can compose and override",
      quote:
        "The payload arc provides a “deferred reference” that can be selectively “loaded” (or unloaded) from a Stage after the stage was initially opened…",
    },
  ],
};

export const REFUSED = {
  question: "What Pyro settings should I use for my smoke shot?",
  rerankScore: -7.7592,
  status: "insufficient_context",
  answer:
    "The retrieved OpenUSD documentation does not provide enough information to answer this question.",
  seconds: 2.6,
};

export const PIPELINE = [
  { label: "Question", note: "" },
  { label: "BM25", note: "SQLite FTS5" },
  { label: "Dense", note: "nomic-embed" },
  { label: "RRF fusion", note: "top 50 + 50" },
  { label: "Reranker", note: "bge-reranker-base" },
  { label: "Refusal gate", note: "fitted on dev" },
  { label: "LLM", note: "Ollama or Gemini" },
  { label: "Quote check", note: "verbatim in chunk" },
];

export const METRICS = [
  { value: 0.834, decimals: 3, suffix: "", label: "nDCG@10", note: "retrieval, held-out" },
  { value: 100, decimals: 0, suffix: "%", label: "correct refusals", note: "all 3 models, dev + held-out" },
  { value: 94, decimals: 0, suffix: "%", label: "valid citations", note: "Gemini Flash-Lite, held-out" },
  { value: 95, decimals: 0, suffix: "%", label: "judge agreement", note: "on facts, κ 0.85" },
];

export const CORPUS = ["OpenUSD 26.08", "76 RST files", "952 chunks", "SHA-256 pinned"];

export const REPO = "github.com/orest-zarutskyi/openusd-docs-assistant";
