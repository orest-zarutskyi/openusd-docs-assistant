import argparse
import json
import sys
from pathlib import Path
from urllib.error import URLError

import uvicorn
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from .adapters import OllamaModels, QdrantIndex, Settings, connect_qdrant
from .api import create_app
from .corpus import fetch_chunks, load_manifest
from .models import DependencyTimeout, DependencyUnavailable
from .questions import load_questions, validate_question_sets
from .retrieval_eval import evaluate_bm25, evaluate_retrieval
from .snapshot import build_manifest, corpus_report, github_file, github_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenUSD Docs Assistant")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "check-corpus", "eval-retrieval"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
        command.add_argument(
            "--source-dir", type=Path, help="Use a verified local source snapshot."
        )
        if name == "check-corpus":
            command.add_argument("--report", type=Path, help="Write chunk statistics as Markdown.")
        if name == "eval-retrieval":
            command.add_argument("--backend", choices=("bm25", "qdrant"), default="bm25")
            command.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    rebuild = commands.add_parser(
        "build-manifest", help="List every docs/**/*.rst at the pinned commit and hash it."
    )
    rebuild.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
    rebuild.add_argument(
        "--snapshot-dir", type=Path, help="Also save the downloaded files for --source-dir."
    )
    check = commands.add_parser("check-questions", help="Validate dev and held-out questions.")
    check.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
    check.add_argument("--source-dir", type=Path, default=Path("data/openusd-26.08"))
    check.add_argument("--dev", type=Path, default=Path("eval/questions.jsonl"))
    check.add_argument("--heldout", type=Path, default=Path("eval/heldout.jsonl"))
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        if args.command == "build-manifest":
            current = json.loads(args.manifest.read_text(encoding="utf-8"))
            manifest = build_manifest(
                current, github_tree, github_file, snapshot_dir=args.snapshot_dir
            )
            text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
            args.manifest.write_text(text, encoding="utf-8", newline="\n")
            load_manifest(args.manifest)
            print(f"OpenUSD {manifest['release']}: {len(manifest['documents'])} documents.")
            return 0
        if args.command == "check-questions":
            sets = {"dev": load_questions(args.dev)}
            if args.heldout.exists():
                sets["heldout"] = load_questions(args.heldout)
            result = validate_question_sets(sets, load_manifest(args.manifest), args.source_dir)
            print(json.dumps(result, indent=2))
            return 1 if result["errors"] else 0
        settings = Settings()
        bm25 = args.command == "eval-retrieval" and args.backend == "bm25"
        if args.command in {"index", "check-corpus"} or bm25:
            manifest = load_manifest(args.manifest)
            chunks = fetch_chunks(manifest, source_dir=args.source_dir)
            if args.command == "check-corpus":
                print(f"OpenUSD {manifest.release}: {len(chunks)} verified chunks.")
                if args.report:
                    args.report.parent.mkdir(parents=True, exist_ok=True)
                    report = corpus_report(manifest, chunks)
                    args.report.write_text(report, encoding="utf-8", newline="\n")
                return 0
            if bm25:
                print(json.dumps(evaluate_bm25(args.questions, chunks, settings.top_k), indent=2))
                return 0

        models = OllamaModels(settings)
        client = connect_qdrant(settings)
        try:
            index = QdrantIndex(client, models, settings)
            if args.command == "index":
                print(f"OpenUSD {manifest.release}: {len(chunks)} verified chunks.")
                changed = index.index(chunks)
                print("Index activated." if changed else "The current index already matches.")
            elif args.command == "eval-retrieval":
                result = evaluate_retrieval(args.questions, index.retrieve, settings.top_k)
                print(json.dumps(result, indent=2))
            else:
                app = create_app(index.retrieve, models.generate, index.ready)
                uvicorn.run(app, host=args.host, port=args.port)
        finally:
            client.close()
    except (
        ValueError,
        URLError,
        OSError,
        DependencyUnavailable,
        DependencyTimeout,
        ResponseHandlingException,
        UnexpectedResponse,
    ) as exc:
        # Provider exceptions contain operational details that should stay off API responses.
        print(f"OpenUSD assistant: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
