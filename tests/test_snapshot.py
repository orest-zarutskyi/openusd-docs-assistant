import hashlib
import json

import pytest

from openusd_assistant.corpus import fetch_chunks, load_manifest
from openusd_assistant.snapshot import build_manifest

CURRENT = {
    "repository": "PixarAnimationStudios/OpenUSD",
    "release": "v26.08",
    "commit": "b" * 40,
    "license": "Example",
    "documents": [],
    "notices": [],
}
FILES = {
    "docs/intro.rst": b"=====\nIntro\n=====\n\nUSD composes layers.\n",
    "docs/user_guides/primvars.rst": b".. _primvars:\n\nPrimvars\n########\n\nText.\n",
    "docs/toc.rst": b".. toctree::\n\n   intro\n",
    "docs/readme.md": b"# Not RST\n",
    "pxr/usd/usd/stage.rst": b"Outside docs\n============\n",
    "LICENSE.txt": b"License",
    "NOTICE.txt": b"Notice",
}


def read(commit: str, path: str) -> bytes:
    assert commit == CURRENT["commit"]
    return FILES[path]


def test_build_manifest_hashes_every_docs_rst_and_saves_a_verifiable_snapshot(tmp_path):
    snapshot = tmp_path / "snapshot"
    manifest = build_manifest(CURRENT, lambda _: list(FILES), read, snapshot_dir=snapshot)

    assert [(d["path"], d["title"]) for d in manifest["documents"]] == [
        ("docs/intro.rst", "Intro"),
        ("docs/toc.rst", "toc"),
        ("docs/user_guides/primvars.rst", "Primvars"),
    ]
    assert manifest["documents"][0]["sha256"] == hashlib.sha256(FILES["docs/intro.rst"]).hexdigest()
    assert [n["path"] for n in manifest["notices"]] == ["LICENSE.txt", "NOTICE.txt"]
    assert manifest["commit"] == CURRENT["commit"]

    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    chunks = fetch_chunks(load_manifest(path), source_dir=snapshot)
    assert {chunk.path for chunk in chunks} == {"docs/intro.rst", "docs/user_guides/primvars.rst"}


def test_build_manifest_rejects_paths_the_loader_would_refuse():
    with pytest.raises(ValueError, match="docs/bad-name.rst"):
        build_manifest(CURRENT, lambda _: ["docs/bad-name.rst"], read)


def test_corpus_report_counts_files_chunks_and_empty_documents(tmp_path):
    from openusd_assistant.snapshot import corpus_report

    snapshot = tmp_path / "snapshot"
    manifest = build_manifest(CURRENT, lambda _: list(FILES), read, snapshot_dir=snapshot)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    loaded = load_manifest(path)
    report = corpus_report(loaded, fetch_chunks(loaded, source_dir=snapshot))
    assert "| RST documents | 3 |" in report
    assert "| Chunks | 2 |" in report
    assert "`docs/toc.rst`" in report.split("Documents without chunks")[1].splitlines()[0]
