# Demo: an answer, its sources and a refusal

Recorded on 2026-11-24 against a local server:

- Model: `qwen3:4b` with thinking, on Ollama.
- Retrieval: hybrid search plus `bge-reranker-base`, `top_k` 8, the settings `/ask` ships with.
- Start command: `openusd-assistant serve --source-dir data/openusd-26.08`.

Responses are copied from `POST /ask`. Long quotes are shortened with `…`, and nothing else is
changed. The same questions can be asked on the page at `http://127.0.0.1:8000/`.

## Motion demo

[openusd-demo.mp4](media/openusd-demo.mp4) (36 s, 1080p) and [openusd-demo.gif](media/openusd-demo.gif) show the two responses below. The reranker scores in the video come from the deployed reranker with the shipped settings: 0.25 for the payload question and −7.76 for the Pyro question, against the current gate of −6.25 ([ADR 15](decisions/0015-refusal-gate-second-pass.md)). The responses below were recorded under the first-pass gate of −0.98; both gates let the payload question through and refuse the Pyro question. Every figure is listed with its source in [demo/src/data.ts](../demo/src/data.ts). To render it again:

```powershell
cd demo
npm install
npm run render
```

Remotion is free for individuals and small teams; larger companies need a company license ([remotion.dev/license](https://www.remotion.dev/license)).

## 1. A question the corpus answers

```json
{"question": "Which composition arc lets me open a stage before loading a heavy asset?"}
```

```json
{
  "status": "answer",
  "answer": "Payload",
  "sources": [
    {
      "path": "docs/maxperf.rst",
      "title": "Package assets with payloads",
      "start_line": 114,
      "end_line": 143,
      "url": "https://github.com/PixarAnimationStudios/OpenUSD/blob/ee47c679abde5b467a7b6a41f3b2285564a4222e/docs/maxperf.rst#L114-L143",
      "quote": "USD provides a composition arc called a :ref:`Payload <glossary:Payload>` that is essentially a \"deferred reference\". It allows us to structure scenes so that we can open a :ref:`Stage <glossary:Stage>` \"unloaded\", …"
    },
    {
      "path": "docs/glossary.rst",
      "title": "Payload",
      "start_line": 2211,
      "end_line": 2239,
      "quote": "When a Stage is opened with :usdcpp:`UsdStage::InitialLoadSet::LoadNone <LoadNone>` specified, Payload arcs are recorded, but not traversed."
    },
    {
      "path": "docs/intro.rst",
      "title": "USD can compose and override:",
      "start_line": 164,
      "end_line": 191,
      "quote": "The :ref:`payload arc<glossary:payload>` provides a \"deferred reference\" that can be selectively \"loaded\" (or unloaded) from a :ref:`glossary:Stage` *after* the stage was initially opened; …"
    }
  ]
}
```

The answer is one word, but each of its three sources links to the exact lines at the pinned
commit. The API returned it only after checking that every quote appears in the chunk it cites.

## 2. A how-to question

```json
{"question": "How do I author a color change inside the red variant instead of writing a local opinion?"}
```

```json
{
  "status": "answer",
  "answer": "To author a color change inside the red variant, you need to first select the red variant using `vset.SetVariantSelection('red')`, then use a `Usd.EditContext` with `vset.GetVariantEditContext()`, and finally set the color attribute with `colorAttr.Set([(1,0,0)])`. …",
  "sources": [
    {
      "path": "docs/tut_authoring_variants.rst",
      "title": "Authoring Variants",
      "start_line": 145,
      "end_line": 207,
      "quote": "To author opinions inside the :usda:`red` variant we first select the variant, then use a :python:`Usd.EditContext`.  This directs editing into the variant."
    }
  ]
}
```

The response took 17 seconds end to end, most of it spent on thinking.

## 3. A question outside the corpus

```json
{"question": "What Pyro settings should I use for my smoke shot?"}
```

```json
{
  "status": "insufficient_context",
  "answer": "The retrieved OpenUSD documentation does not provide enough information to answer this question.",
  "sources": []
}
```

The reranker's best score fell below the refusal gate fitted on dev, so the model was never
called. The response took 2.6 seconds, which is the time of retrieval alone.
