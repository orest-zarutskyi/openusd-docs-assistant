"""Compare model quotes with RST source text while ignoring markup, not wording."""

import re
from typing import Literal

# :ref:`label <target>`, :sdfpath:`/A` -> label, /A (a quote may stop before the target)
_ROLE = re.compile(r":[\w+.:-]+:`([^`<]*?)(?:\s*<[^>`]*>)?`")
# `label <url>`_ and `label <url>`__ -> label
_LINK = re.compile(r"`([^`<]*?)\s*<[^>`]*>`_{0,2}")
# heading underlines and transitions such as ##### or -----
_RULE = re.compile(r"([=\-~^#*+_.:`])\1{3,}")
_ELLIPSIS = re.compile(r"^(?:\.\.\.|…)\s*|\s*(?:\.\.\.|…)$")


def normalize_rst(text: str) -> str:
    """Drop roles, link targets, rules and inline markup; keep every word and its order."""
    text = _ROLE.sub(r"\1", text)
    text = _LINK.sub(r"\1", text)
    text = _RULE.sub(" ", text)
    text = re.sub(r"`_{1,2}", "`", text)  # `name`_ reference
    text = text.replace("`", "").replace("*", "")
    return " ".join(text.split())


def quote_in_text(quote: str, text: str) -> bool:
    """True if the quote, without markup and edge ellipses, appears in the chunk text."""
    needle = _ELLIPSIS.sub("", normalize_rst(quote)).strip()
    return bool(needle) and needle in normalize_rst(text)


# Citation checks, each including the previous one (ADR 16).
CitationCheck = Literal["strict", "reattribute", "lenient", "fragments"]
CITATION_CHECKS: tuple[CitationCheck, ...] = ("strict", "reattribute", "lenient", "fragments")

# :ref:`glossary:Stage` (no label) renders as the target's title; keep the last segment.
_REF_TARGET = re.compile(r":ref:`([^`<]*?)`")
_QUOTE_MARKS = re.compile("[\"'\u201c\u201d\u2018\u2019]")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?)])")
_SPLIT = re.compile(r"\s*(?:\.\.\.|\u2026)\s*|(?<=[.!?])\s+")
_TRAILING_PUNCT = ".,;:!?"


def normalize_lenient(text: str) -> str:
    """normalize_rst, then also ignore case, quote marks and spaces before punctuation."""
    text = _REF_TARGET.sub(lambda m: m.group(1).split(":")[-1], text)
    text = normalize_rst(text)
    text = _QUOTE_MARKS.sub("", text)
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    return " ".join(text.lower().split())


def _lenient_needle(quote: str) -> str:
    needle = _ELLIPSIS.sub("", normalize_lenient(quote)).strip()
    return needle.rstrip(_TRAILING_PUNCT).strip()


def match_quote(quote: str, text: str, check: CitationCheck = "strict") -> str | None:
    """The quote as shown to the reader if ``text`` supports it under ``check``, else None.

    strict and reattribute compare word-exact after markup normalization (reattribute differs
    only in which chunk the caller may search). lenient also ignores case, quote marks, spaces
    before punctuation and trailing punctuation. fragments also accepts a quote split at
    ellipses or sentence ends when every fragment (three words or more) appears in order; it is
    then shown with " \u2026 " between the fragments. No check accepts a word the text lacks.
    """
    if quote_in_text(quote, text):
        return quote
    if check in ("strict", "reattribute"):
        return None
    haystack = normalize_lenient(text)
    needle = _lenient_needle(quote)
    if needle and needle in haystack:
        return quote
    if check != "fragments":
        return None
    parts = [p.strip() for p in _SPLIT.split(_ELLIPSIS.sub("", quote.strip())) if p.strip()]
    if len(parts) < 2:
        return None
    position = 0
    for part in parts:
        fragment = _lenient_needle(part)
        if len(fragment.split()) < 3:
            return None
        found = haystack.find(fragment, position)
        if found < 0:
            return None
        position = found + len(fragment)
    return " \u2026 ".join(parts)
