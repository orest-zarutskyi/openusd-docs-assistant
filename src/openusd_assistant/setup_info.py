"""Describe the machine, versions and data behind an evaluation run for its report."""

import datetime
import os
import platform
import subprocess
from collections import Counter

import httpx

from .corpus import Manifest
from .models import Chunk
from .questions import Question


def _run(*command: str) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _ollama(settings) -> tuple[str, str]:
    try:
        version = httpx.get(f"{settings.ollama_url}/api/version", timeout=5).json()["version"]
        tags = httpx.get(f"{settings.ollama_url}/api/tags", timeout=5).json()["models"]
        digest = next(
            (m["digest"][:12] for m in tags if m["name"] == settings.embedding_model), "unknown"
        )
        return version, digest
    except (httpx.HTTPError, KeyError, ValueError):
        return "unknown", "unknown"


def describe_setup(
    settings, manifest: Manifest, chunks: list[Chunk], questions: list[Question], args
) -> list[str]:
    kinds = Counter(q.kind for q in questions)
    ollama_version, digest = _ollama(settings)
    gpu = _run("nvidia-smi", "--query-gpu=name", "--format=csv,noheader")
    commit = _run("git", "rev-parse", "--short", "HEAD")
    dirty = " (with uncommitted changes)" if _run("git", "status", "--porcelain") else ""
    return [
        f"- Date: {datetime.date.today().isoformat()}; code commit `{commit}`{dirty}.",
        f"- Corpus: OpenUSD {manifest.release} `{manifest.commit[:12]}`, "
        f"{len(manifest.documents)} documents, {len(chunks)} chunks.",
        f"- Questions: `{args.questions.as_posix()}`, {len(questions)} total: "
        + ", ".join(f"{count} {kind}" for kind, count in sorted(kinds.items()))
        + ".",
        f"- Dense: `{settings.embedding_model}` (digest `{digest}`) on Ollama {ollama_version}, "
        "embedded Qdrant, cosine similarity.",
        f"- Hybrid: RRF k=60 over the top {settings.candidate_depth} BM25 and dense candidates; "
        f"rerank rescores the top {settings.rerank_depth} fused candidates with fastembed (ONNX, CPU).",
        f"- Machine: {platform.system()} {platform.release()}, {os.cpu_count()} logical CPUs "
        f"({_cpu_name()}), GPU {gpu}. Latency is wall time per query in one warm process.",
    ]


def _cpu_name() -> str:
    if platform.system() == "Windows":
        return _run(
            "powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"
        )
    return platform.processor() or "unknown"
