# 16. Choose how strictly citations are checked, by a rule fixed in advance

Status: proposed, 2026-11-25. The variants and rule below were committed before any comparison ran.

## Context

On the second-pass dev baseline, 20 answers (across the three models) failed the citation check
([9](0009-verbatim-quotes-with-rst-normalization.md)). Of their 26 failing quotes:

- **19 quote the right passage**, but the check misses a formatting difference:
  - a `:ref:` target kept with its prefix (`glossary:Stage` where the rendered text says `Stage`);
  - a space before a comma;
  - quote marks or asterisks around a term (`"model"` against `*model*`);
  - a period added where the quote stops mid-sentence;
  - a capital letter after the model dropped the leading "An";
  - two verbatim sentences from one chunk joined without the text between them.
- **4 are verbatim**, but cite the id of a different retrieved chunk than the one containing them.
- **1** uses an inner ellipsis whose parts are each verbatim.
- **2 are paraphrases** that the source does not contain.

## Variants

Each variant includes the previous one:

- **C0, strict:** the current check, word-exact after markup normalization, against the cited chunk.
- **C1, reattribute:** if the cited chunk does not contain the quote but another retrieved chunk
  does, under C0's rule, cite that chunk instead.
- **C2, lenient:** C1, and both sides are also normalized by:
  - ignoring letter case;
  - ignoring quote characters;
  - dropping whitespace before punctuation;
  - reducing `:ref:` targets to their last segment;
  - trimming trailing punctuation from the quote.

  Every word must still appear in order.
- **C3, fragments:** C2, and a quote may also be split at ellipses and sentence ends. Every
  fragment must be at least three words and found in the same chunk in order. The quote is then
  shown as its fragments joined by " … ", so the reader sees that it is not one continuous
  passage.

None of the variants accepts a quote with a word that is not in the source.

## Evaluation

The check changes only how saved answers are judged, not what the models wrote. Each variant is
therefore applied to the saved second-pass dev answers (`reports/answers/pass2_dev_baseline/`
plus `pass2_dev_nogate/`), with the deployed gate (−6.2459, [15](0015-refusal-gate-second-pass.md)).
No model is called again.

## Selection rule

1. Per variant and per model, compute the variant score
   ([8](0008-pre-registered-selection-rules.md)):
   (answerable answered with valid citations + correct refusals) / 2.
2. Exclude a variant if it makes any unanswerable question count as answered.
3. Pick the highest mean score over the three models. Variants within half an answerable question
   of the best are decided by the stricter one (C0 < C1 < C2 < C3).
4. The report lists every quote a variant newly accepts, next to the source text that matched it,
   so the acceptance can be audited.

## Consequences

Filled in after the comparison.
