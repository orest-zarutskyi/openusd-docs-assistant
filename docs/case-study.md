# Case study: a USD consultant for Solaris artists

## Problem

Artists and TDs in Solaris often have USD questions that the official documentation answers: why
a payload is not loading, how a variant is selected from a stronger layer, which arc to use. The
documentation is long and spread over 76 files, and a general-purpose chatbot answers confidently
whether or not it knows. The goal was an assistant that answers only from the documentation,
shows the passage it relied on, and says when the documentation does not cover the question.

## Approach

- **Fixed source.** The corpus is the RST documentation of OpenUSD 26.08, pinned by commit and
  SHA-256, split into chunks that keep their exact line ranges, so every citation links to real
  upstream lines.
- **Retrieval.** BM25 and dense search are fused with reciprocal rank fusion and reranked by a
  cross-encoder. A score threshold refuses questions far from the corpus.
- **Checked answers.** The model must return JSON with an answer and a literal quote for each
  claim. The API rejects an answer whose quotes are not in the retrieved passages.
- **Where artists work.** A Houdini panel docks next to the Scene Graph Tree and can add the
  selected prim (type, arcs, variants, schemas) to the question.
- **Evaluation discipline.** Every setting was chosen on a dev set by a rule written down and
  committed before the comparison ran. After each of four passes, the settings were frozen and run
  once on a held-out set the system had not seen; the set was then folded into dev. The last two
  held-out sets are 106 real questions from public forums.

## Results

On the 70 answerable forum questions of held-out v3 and v4, Gemini 3.5 Flash-Lite answered 52 with
valid citations and refused 35 of the 36 unanswerable ones. The judge found 96–97% of its answers
fully supported by the quoted passages. It costs about $0.16 per 100 questions at list price and
answers in about 5 s.

## What worked

- **The citation check.** Requiring literal quotes and verifying them turns an unsupported quote
  into a visible rejection instead of a plausible wrong answer.
- **Writing the rule first.** Several changes that looked promising were rejected by their own
  pre-registered rule, and the records keep those results.
- **Real questions.** Questions written from the documentation were easier: held-out v2, written
  by the author, gave retrieval nDCG@10 0.672; the first forum set gave 0.557.

## What did not

- **A stricter refusal gate.** The first gate refused 20 of 48 answerable questions on held-out v2.
  It was replaced by a safety net that keeps every answerable dev question; on the forum sets it
  refused almost nothing, so refusals come from the model.
- **Relaxed prompt wording.** Allowing partial answers did not turn refusals into answers in two
  separate tests: qwen3:4b's refusals became invalid output, and qwen3.5:4b and qwen3.5:9b refused
  more.
- **Choosing the local model on dev.** qwen3.5:9b won on dev, but on both forum sets it answered
  fewer questions than qwen3:4b. qwen3:4b, in turn, claimed answers to unanswerable questions more
  often. Neither matches Flash-Lite.

## Next steps

Retrieval is the weakest stage on real questions. The next candidates are query rewriting,
re-chunking very large sections, and more forum-style dev questions so that the local model choice
is made on the kind of question it will meet.

Details: [evaluation](evaluation.md), [decision records](decisions/README.md),
[Houdini package](../integrations/houdini/README.md).
