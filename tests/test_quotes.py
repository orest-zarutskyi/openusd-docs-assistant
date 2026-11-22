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
