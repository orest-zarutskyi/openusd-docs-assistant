"""Apply the independent review of the evaluation questions (2026-11-23).

A separate review checked all 56 questions against the snapshot; every finding applied here
was confirmed against the cited RST lines.
Run once from the project root: python eval/review_fixes.py
"""

from pathlib import Path

from openusd_assistant.questions import Question, dump_questions, load_questions


def alt(path: str, start: int, end: int) -> dict:
    return {"path": f"docs/{path}", "start_line": start, "end_line": end, "alternative": True}


ALTERNATIVES = {
    # dev
    "payload": [
        alt("glossary.rst", 1817, 1822),
        alt("maxperf.rst", 121, 125),
        alt("glossary.rst", 2219, 2227),
    ],
    "sublayers": [alt("glossary.rst", 3491, 3492), alt("glossary.rst", 1576, 1578)],
    "stage": [alt("tut_helloworld_redux.rst", 28, 34)],
    "default-prim": [alt("tut_xforms.rst", 621, 624)],
    "add-reference": [alt("tut_referencing_layers.rst", 184, 191)],
    "timecodes-per-second": [alt("user_guides/time_and_animated_values.rst", 184, 216)],
    "indexed-primvars": [alt("user_guides/render_user_guide.rst", 648, 652)],
    "face-varying": [alt("user_guides/render_user_guide.rst", 631, 641)],
    "layer-offset-scale": [alt("tut_xforms.rst", 599, 603)],
    "attribute-block": [alt("user_guides/time_and_animated_values.rst", 824, 867)],
    "reversible-hide": [alt("intro.rst", 209, 218)],
    "lightweight-asset-open": [alt("glossary.rst", 2219, 2239)],
    "working-set": [alt("intro.rst", 179, 184), alt("glossary.rst", 2219, 2227)],
    "active-vs-visibility": [alt("user_guides/render_user_guide.rst", 110, 115)],
    "constant-vs-uniform": [alt("user_guides/render_user_guide.rst", 621, 624)],
    # held-out
    "primvar-modes": [alt("user_guides/render_user_guide.rst", 617, 633)],
    "stage-traverse": [alt("glossary.rst", 3443, 3448)],
    "usdcat-to-text": [alt("tut_converting_between_layer_formats.rst", 89, 111)],
    "collection-modes": [alt("user_guides/collections_and_patterns.rst", 173, 185)],
    "broadcast-edit": [alt("intro.rst", 193, 203)],
    "helper-geometry-in-renders": [alt("user_guides/render_user_guide.rst", 196, 206)],
    "move-without-touching-source": [
        alt("glossary.rst", 2727, 2735),
        alt("user_guides/namespace_editing.rst", 102, 135),
    ],
    # The reference-path example sits at lines 25-47; lines 19-23 are dev's expression-targets.
    "switchable-asset-root": [alt("user_guides/variable_expressions.rst", 25, 47)],
    "over-vs-def": [alt("glossary.rst", 824, 833), alt("glossary.rst", 1986, 1996)],
    "specializes-vs-inherits": [alt("intro.rst", 193, 203)],
    "usda-vs-usdc": [alt("glossary.rst", 777, 797)],
}

# Usdvol's table of contents names ParticleField3DGaussianSplat and its attribute APIs,
# so the question is partly answered by the corpus and is no longer a clean refusal.
DROP = {"gaussian-splats"}


def edit(q: dict) -> dict:
    if q["id"] == "working-set":
        # The old wording copied glossary.rst:1826-1827, so it was not a paraphrase.
        q["question"] = (
            "Our city set is huge. Can I keep most of it out of memory and only pay "
            "the cost of the buildings I'm currently working on?"
        )
    if q["id"] == "broadcast-edit":
        # The old wording copied glossary.rst:1127-1128.
        q["question"] = (
            "How can I tweak every tree in my forest at once without editing each tree's file?"
        )
    if q["id"] == "active-vs-visibility":
        # The glossary contrasts the two right after the cited span (lines 4253-4257).
        q["sources"][1]["end_line"] = 4257
        q["expected_facts"].append(
            "Invisible geometry stays available for inspection and positioning; deactivated prims do not."
        )
        q.pop("uncertain", None)
    if q["id"] == "collection-modes":
        # Lines 173-177: both kinds of property may be authored, but only one mode is used.
        q["expected_facts"] = [
            "Relationship-mode uses target-based include and exclude rules.",
            "Expression-mode uses pattern-based expressions.",
            "A collection uses only one mode at a time; properties for the other mode are ignored.",
            "The mode attribute selects the mode.",
        ]
    if q["id"] in {"nucleus-live-sync", "storm-vram"}:
        q.pop("uncertain", None)  # the review found no answer anywhere in the corpus
    q["sources"] = q.get("sources", []) + ALTERNATIVES.get(q["id"], [])
    return q


def main() -> None:
    for path in (Path("eval/questions.jsonl"), Path("eval/heldout.jsonl")):
        questions = load_questions(path)
        if any(s.alternative for q in questions for s in q.sources):
            raise SystemExit(f"{path} already has alternative sources; fixes were applied")
        fixed = [
            Question.model_validate(edit(q.model_dump(exclude_none=True)))
            for q in questions
            if q.id not in DROP
        ]
        path.write_text(dump_questions(fixed), encoding="utf-8", newline="\n")
        print(f"{path}: {len(questions)} -> {len(fixed)} questions")


if __name__ == "__main__":
    main()
