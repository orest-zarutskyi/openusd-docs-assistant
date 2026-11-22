"""Load a pinned OpenUSD documentation snapshot without rendering its RST."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import HTTPRedirectHandler, build_opener
from uuid import NAMESPACE_URL, uuid5

from .models import Chunk

_REPOSITORY = "PixarAnimationStudios/OpenUSD"
_DOCUMENT = re.compile(r"docs/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+\.rst")
_NOTICES = {"LICENSE.txt", "NOTICE.txt"}
_MAX_SOURCE_BYTES = 2 * 1024 * 1024
_HEADING_RULE = re.compile(r"([=!~^`#*+_.:\-])\1{2,}")


@dataclass(frozen=True)
class SourceFile:
    path: str
    sha256: str
    title: str = ""


@dataclass(frozen=True)
class Manifest:
    release: str
    commit: str
    license: str
    documents: tuple[SourceFile, ...]
    notices: tuple[SourceFile, ...]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def load_manifest(path: Path) -> Manifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["repository"] != _REPOSITORY:
        raise ValueError("The only supported source repository is OpenUSD")
    if not re.fullmatch(r"[a-f0-9]{40}", data["commit"]):
        raise ValueError("The corpus must use a full commit SHA")
    documents = tuple(SourceFile(**entry) for entry in data["documents"])
    notices = tuple(SourceFile(**entry) for entry in data["notices"])
    if not documents or any(
        not _DOCUMENT.fullmatch(file.path) or not file.title for file in documents
    ):
        raise ValueError("Invalid OpenUSD document path or missing title")
    if len(notices) != len(_NOTICES) or {file.path for file in notices} != _NOTICES:
        raise ValueError("The OpenUSD license and notice must both be included")
    files = (*documents, *notices)
    if len({file.path for file in files}) != len(files):
        raise ValueError("Duplicate source path")
    if any(not re.fullmatch(r"[a-f0-9]{64}", file.sha256) for file in files):
        raise ValueError("Each source requires a SHA-256 digest")
    return Manifest(data["release"], data["commit"], data["license"], documents, notices)


def fetch_chunks(manifest: Manifest, *, source_dir: Path | None = None) -> list[Chunk]:
    if source_dir is None:
        opener = build_opener(_NoRedirect)

        def read(file: SourceFile) -> bytes:
            url = f"https://raw.githubusercontent.com/{_REPOSITORY}/{manifest.commit}/{file.path}"
            with opener.open(url, timeout=20) as response:
                return response.read(_MAX_SOURCE_BYTES + 1)
    else:

        def read(file: SourceFile) -> bytes:
            with source_dir.joinpath(file.path).open("rb") as stream:
                return stream.read(_MAX_SOURCE_BYTES + 1)

    chunks = []
    for file in (*manifest.notices, *manifest.documents):
        content = read(file)
        if len(content) > _MAX_SOURCE_BYTES or hashlib.sha256(content).hexdigest() != file.sha256:
            raise ValueError(f"OpenUSD snapshot integrity check failed for {file.path}")
        if file in manifest.documents:
            chunks.extend(split_document(file, manifest.commit, content.decode("utf-8")))
    if not chunks:
        raise ValueError("No documentation chunks could be read")
    return chunks


def split_document(
    file: SourceFile, commit: str, text: str, *, chunk_chars: int = 2300
) -> list[Chunk]:
    """Split on headings and top-level paragraphs, preserving source line ranges."""
    lines = text.splitlines()
    headings = _headings(lines)
    headings.setdefault(0, file.title)
    starts = [*sorted(headings), len(lines)]
    chunks = []
    for start, end in zip(starts, starts[1:]):
        title = headings[start]
        for first, stop in _paragraph_chunks(lines, start, end, chunk_chars):
            source = lines[first:stop]
            if not any(line.strip() and not line.startswith(".. include::") for line in source):
                continue
            start_line, end_line = first + 1, stop
            url = f"https://github.com/{_REPOSITORY}/blob/{commit}/{file.path}#L{start_line}-L{end_line}"
            chunks.append(
                Chunk(
                    id=str(uuid5(NAMESPACE_URL, url)),
                    path=file.path,
                    title=title,
                    start_line=start_line,
                    end_line=end_line,
                    text="\n".join(source),
                    url=url,
                )
            )
    return chunks


def _headings(lines: list[str]) -> dict[int, str]:
    result = {}
    for i, (line, underline) in enumerate(zip(lines, lines[1:])):
        if not line or line[0].isspace() or line.startswith(".. ") or _HEADING_RULE.fullmatch(line):
            continue
        if len(underline) < len(line) or not _HEADING_RULE.fullmatch(underline):
            continue
        start = i - 1 if i > 0 and lines[i - 1] == underline else i
        result[start] = line
    return result


def _paragraph_chunks(
    lines: list[str], start: int, end: int, chunk_chars: int
) -> list[tuple[int, int]]:
    boundaries = [start]
    for i in range(start + 1, end):
        if not lines[i - 1].strip() and lines[i] and not lines[i][0].isspace():
            boundaries.append(i)
    boundaries.append(end)

    sections = []
    chunk_start, size = start, 0
    for left, right in zip(boundaries, boundaries[1:]):
        block_size = sum(len(line) + 1 for line in lines[left:right])
        if size and size + block_size > chunk_chars:
            sections.append((chunk_start, left))
            chunk_start, size = left, 0
        size += block_size
    sections.append((chunk_start, end))

    trimmed = []
    for left, right in sections:
        while left < right and not lines[left].strip():
            left += 1
        while left < right and not lines[right - 1].strip():
            right -= 1
        if left < right:
            trimmed.append((left, right))
    return trimmed
