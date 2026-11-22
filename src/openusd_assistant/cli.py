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
from .retrieval_eval import evaluate_bm25, evaluate_retrieval


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenUSD Docs Assistant")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "check-corpus", "eval-retrieval"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
        command.add_argument(
            "--source-dir", type=Path, help="Use a verified local source snapshot."
        )
        if name == "eval-retrieval":
            command.add_argument("--backend", choices=("bm25", "qdrant"), default="bm25")
            command.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        settings = Settings()
        bm25 = args.command == "eval-retrieval" and args.backend == "bm25"
        if args.command in {"index", "check-corpus"} or bm25:
            manifest = load_manifest(args.manifest)
            chunks = fetch_chunks(manifest, source_dir=args.source_dir)
            if args.command == "check-corpus":
                print(f"OpenUSD {manifest.release}: {len(chunks)} verified chunks.")
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
