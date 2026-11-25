# 16. Choose how strictly citations are checked, by a rule fixed in advance

Status: accepted, 2026-11-25. The variants and rule below were committed before any comparison ran (commit `cf317e9`).

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

## Result

`reports/pass2/citations_dev.md`. Under strict checking the replay gives the same score as the gate comparison (0.867), so the two analyses agree.

| Check | Mean score | Unanswerable answered | Flash-Lite | qwen3.5:4b | qwen3:4b |
| --- | --- | --- | --- | --- | --- |
| strict | 0.867 | 0 | 39 | 26 | 32 |
| reattribute | 0.875 | 0 | 39 | 27 | 33 |
| lenient | 0.905 | 0 | 41 | 30 | 36 |
| **fragments** | **0.917** | 0 | 41 | 32 | 37 |

The last three columns count answerable dev questions (of 44) answered with valid citations. The rule picks `fragments`, and `/ask` now uses `citation_check = "fragments"`.

The report lists every newly accepted quote with the chunk that supports it. None adds a word the source lacks. The two known paraphrases (`reversible-hide` from Flash-Lite and `switchable-asset-root` from qwen3.5:4b) are still rejected.

## Consequences

- On dev, answerable questions answered with valid citations rise by 2 (Flash-Lite), 6 (qwen3.5:4b) and 5 (qwen3:4b). The local models gained most, because they reproduce markup and punctuation less faithfully.
- A quote shown to the reader is the model's text. Its case or quote marks may differ from the source, but its words are the source's, in order. A quote stitched from separate sentences is shown with " … " between the pieces.
- Short verbatim fragments (three words or more) now pass, so the check proves that the words are in the cited passage, not that the passage supports the answer. Whether it does is still measured separately by the judge ([13](0013-llm-judge-and-calibration.md)).
- Reports keep the strict per-quote `quote_validity` metric, so the two levels stay comparable with the first pass.
