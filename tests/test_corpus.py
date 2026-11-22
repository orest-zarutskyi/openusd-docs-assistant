import hashlib
import json
from pathlib import Path

import pytest

from openusd_assistant.corpus import SourceFile, fetch_chunks, load_manifest, split_document


def test_chunks_preserve_line_numbers_and_code_blocks():
    content = "\n".join(
        [
            ".. include:: ignored.rst",
            "",
            "USD stage",
            "=========",
            "",
            "Create a stage and save its root layer.",
            "",
            ".. code-block:: python",
            "",
            "   stage = Usd.Stage.CreateNew('demo.usda')",
            "   stage.GetRootLayer().Save()",
            "",
            "References",
            "----------",
            "",
            "A reference lets a scene assemble assets.",
        ]
    )
    file = SourceFile("docs/demo.rst", "", "Demo")
    chunks = split_document(file, "a" * 40, content, chunk_chars=55)

    assert chunks == split_document(file, "a" * 40, content, chunk_chars=55)
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    code = next(chunk for chunk in chunks if "code-block" in chunk.text)
    assert code.title == "USD stage"
    assert code.start_line == 8
    assert code.end_line == 11
    assert code.text.endswith("   stage.GetRootLayer().Save()")
    assert code.url.endswith("/docs/demo.rst#L8-L11")
    assert all(
        chunk.text == "\n".join(content.splitlines()[chunk.start_line - 1 : chunk.end_line])
        for chunk in chunks
    )


@pytest.fixture
def snapshot(tmp_path: Path) -> tuple[Path, Path]:
    source_dir = tmp_path / "source"
    payloads = {
        "docs/demo.rst": b"USD stage\n=========\n\nThe root layer may be saved.\n",
        "LICENSE.txt": b"License contents",
        "NOTICE.txt": b"Notice contents",
    }
    files = {}
    for name, content in payloads.items():
        file = source_dir / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        files[name] = dict(path=name, sha256=hashlib.sha256(content).hexdigest())
    manifest = {
        "repository": "PixarAnimationStudios/OpenUSD",
        "release": "v26.08",
        "commit": "a" * 40,
        "license": "Example",
        "documents": [dict(files["docs/demo.rst"], title="Demo")],
        "notices": [files["LICENSE.txt"], files["NOTICE.txt"]],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, source_dir


def test_local_snapshot_validates_source_and_notices(snapshot):
    manifest_path, source_dir = snapshot
    manifest = load_manifest(manifest_path)
    assert "root layer may be saved" in fetch_chunks(manifest, source_dir=source_dir)[0].text
    (source_dir / "NOTICE.txt").write_text("bad", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity check failed for NOTICE.txt"):
        fetch_chunks(manifest, source_dir=source_dir)


@pytest.mark.parametrize(
    "path", ["docs/../secret.txt", "docs/a/../b.rst", "docs//b.rst", "docs/b.md", "/docs/b.rst"]
)
def test_manifest_rejects_unapproved_paths(snapshot, path):
    manifest_path, _ = snapshot
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["documents"][0]["path"] = path
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid OpenUSD document path"):
        load_manifest(manifest_path)


def test_manifest_accepts_nested_documentation(snapshot):
    manifest_path, _ = snapshot
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["documents"][0]["path"] = "docs/user_guides/schemas/index.rst"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert load_manifest(manifest_path).documents[0].path == "docs/user_guides/schemas/index.rst"
