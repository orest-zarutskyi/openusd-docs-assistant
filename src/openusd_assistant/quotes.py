"""Compare model quotes with RST source text while ignoring markup, not wording."""

import re

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
