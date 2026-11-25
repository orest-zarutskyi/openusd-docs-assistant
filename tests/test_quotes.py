import pytest

from openusd_assistant.quotes import normalize_rst, quote_in_text

SOURCE = """You can "stack" USD layers together using the :ref:`subLayers composition arc
<glossary:SubLayers>`, forming ordered (nestable) :ref:`"LayerStacks" <glossary:LayerStack>`.
If the `resolved value <#usdglossary-valueresolution>`_ is **invisible**, then neither
the prim itself nor any prims in the subtree rooted at the prim should be rendered.

Use binary ".usd" files for geometry and shading caches
#######################################################

Call :python:`stage.GetRootLayer().Save()` to save ``HelloWorld.usda``."""


@pytest.mark.parametrize(
    "quote",
    [
        # Quote stops inside a role, before its <target>.
        'You can "stack" USD layers together using the :ref:`subLayers composition arc`',
        # Edge ellipsis plus a complete role.
        '...ordered (nestable) :ref:`"LayerStacks" <glossary:LayerStack>`',
        # Markup dropped entirely by the model.
        "If the resolved value is invisible, then neither the prim itself",
        # A heading quoted with a shorter underline.
        'Use binary ".usd" files for geometry and shading caches\n#########',
        "Call stage.GetRootLayer().Save() to save HelloWorld.usda.",
    ],
)
def test_markup_differences_are_ignored(quote):
    assert quote_in_text(quote, SOURCE)


@pytest.mark.parametrize(
    "quote",
    [
        "forming ordered (nestable) LayerStacks",  # dropped the quotation marks: wording differs
        "If the resolved value is hidden",  # changed word
        "neither the prim should be rendered",  # words skipped
        "Layers can be stacked with subLayers",  # paraphrase
        "**",  # markup only
        "...",
        "glossary:SubLayers",  # a link target is not quotable text
    ],
)
def test_wording_must_still_match(quote):
    assert not quote_in_text(quote, SOURCE)


def test_ellipsis_is_only_trimmed_at_the_edges():
    assert not quote_in_text("You can ... USD layers", SOURCE)
    assert quote_in_text("…the prim itself nor any prims…", SOURCE)


def test_normalize_keeps_words_and_order():
    assert normalize_rst(":ref:`Payload <glossary:Payload>` arcs") == "Payload arcs"
    assert normalize_rst("`docs <https://x.invalid>`__ and `name`_") == "docs and name"
    assert normalize_rst("*Activation* is ``on``") == "Activation is on"


LENIENT_SOURCE = (
    "USD provides a composition arc called a :ref:`Payload <glossary:Payload>` that is\n"
    'essentially a "deferred reference". It is loaded from a :ref:`glossary:Stage` after\n'
    'the stage was opened. An *over* is the "weakest" of the three specifiers, in that it\n'
    "does not change the resolved specifier. Note that this is a rule. The *model* kind is\n"
    "considered an abstract type."
)


def test_strict_and_reattribute_keep_the_word_exact_check():
    from openusd_assistant.quotes import match_quote

    quote = "It is loaded from a glossary:Stage after the stage was opened"
    for check in ("strict", "reattribute"):
        assert match_quote(quote, LENIENT_SOURCE, check) == quote
        assert (
            match_quote("It is loaded from a Stage after the stage", LENIENT_SOURCE, check) is None
        )


def test_lenient_ignores_case_quote_marks_refs_and_trailing_punctuation():
    from openusd_assistant.quotes import match_quote

    for quote in (
        "It is loaded from a Stage after the stage was opened.",  # :ref: target, period
        "Over is the weakest of the three specifiers , in that it",  # case, quotes, space
        '"model" kind is considered an abstract type',  # quote marks for asterisks
    ):
        assert match_quote(quote, LENIENT_SOURCE, "lenient") == quote
        assert match_quote(quote, LENIENT_SOURCE, "strict") is None
    # Still word-exact: a changed or added word fails.
    assert (
        match_quote("Over is the strongest of the three specifiers", LENIENT_SOURCE, "lenient")
        is None
    )
    assert match_quote("It is lazily loaded from a Stage", LENIENT_SOURCE, "lenient") is None


def test_fragments_accepts_verbatim_pieces_in_order_and_marks_the_gap():
    from openusd_assistant.quotes import match_quote

    quote = "the stage was opened. Note that this is a rule."
    assert match_quote(quote, LENIENT_SOURCE, "lenient") is None
    assert (
        match_quote(quote, LENIENT_SOURCE, "fragments")
        == "the stage was opened. … Note that this is a rule."
    )
    joined = "USD provides a composition arc ... does not change the resolved specifier"
    assert match_quote(joined, LENIENT_SOURCE, "fragments") is not None
    # Out of order, too short, or a piece that is not in the source.
    assert (
        match_quote("Note that this is a rule. the stage was opened.", LENIENT_SOURCE, "fragments")
        is None
    )
    assert match_quote("It is. Note that this is a rule.", LENIENT_SOURCE, "fragments") is None
    assert (
        match_quote("the stage was opened. This rule is new here.", LENIENT_SOURCE, "fragments")
        is None
    )


def test_verified_answer_reattributes_only_above_strict():
    import pytest

    from openusd_assistant.graph import _verified_answer
    from openusd_assistant.models import Chunk, DraftAnswer, InvalidModelOutput

    def chunk(cid, text):
        return Chunk(
            id=cid,
            path="docs/x.rst",
            title="X",
            start_line=1,
            end_line=2,
            text=text,
            url="https://x.invalid/",
        )

    context = [chunk("a", "Something else entirely here."), chunk("b", LENIENT_SOURCE)]
    draft = DraftAnswer(
        status="answer",
        answer="Payload.",
        evidence=[{"chunk_id": "a", "quote": "a composition arc called a Payload"}],
    )
    with pytest.raises(InvalidModelOutput):
        _verified_answer(draft, context, "strict")
    result = _verified_answer(draft, context, "reattribute")
    assert result.sources[0].chunk_id == "b"
