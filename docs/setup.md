# Setup

## Local install

Use Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Run the commands from the project root.

```powershell
uv sync --locked --extra dev
uv run --locked openusd-assistant check-corpus
uv run --locked openusd-assistant eval-retrieval --modes bm25
uv run --locked --extra dev pytest
```

For an existing snapshot, pass `--source-dir data/openusd-26.08` to `check-corpus`, `index`, `serve` or the evaluations. The directory should contain the 76 files listed in the manifest under `docs/`, plus the original `LICENSE.txt` and `NOTICE.txt`. `openusd-assistant build-manifest --snapshot-dir data/openusd-26.08` downloads them.

For live generation, copy `.env.example` to `.env`. Start [Ollama](https://ollama.com/) on the host, pull the models below, and select the Qdrant storage. For a single local process without Docker, set `OPENUSD_QDRANT_PATH` to `data/qdrant` in `.env`. Run the indexer before starting the API, because Qdrant's embedded storage accepts a single process at a time. The reranker is downloaded into `data/fastembed` on first use.

```powershell
ollama pull qwen3.5:9b
ollama pull nomic-embed-text:v1.5
uv run --locked openusd-assistant index
uv run --locked openusd-assistant serve
```

To answer with Gemini instead, set `OPENUSD_CHAT_PROVIDER=gemini`, `OPENUSD_GEMINI_MODEL=gemini-3.5-flash-lite` and `OPENUSD_GEMINI_API_KEY` in `.env`. Embeddings still use Ollama. Keep keys only in `.env`, which Git ignores.

Open [localhost:8000](http://127.0.0.1:8000/) for a simple question page, or [localhost:8000/docs](http://127.0.0.1:8000/docs) for the API. Try “Which composition arc lets me open a stage before loading a heavy asset?” and “What Pyro settings should I use for my smoke shot?” The first question is covered by the corpus. The second is a refusal case.

## Docker Compose

With Docker Desktop (on Windows it needs WSL 2) and host Ollama running, build and start the services, then index the corpus. The API container downloads and verifies the corpus, and on first start the reranker, so `/readyz` turns ready after a minute or two. The API is available on loopback only. For other host layouts, set `OPENUSD_DOCKER_OLLAMA_URL` to the host model service address reachable from the API container. It is separate from `OPENUSD_OLLAMA_URL`, which points at `127.0.0.1` for local runs.

```powershell
docker compose up -d --build
docker compose run --rm api index
```

## Pipeline and indexing

```text
Pinned docs → verify SHA-256 → split by source lines → index in Qdrant and SQLite FTS5
Question → FastAPI → LangGraph retrieve (BM25 + dense → RRF → rerank → gate)
         → generate → verify quotes → answer
                    ↘ gate not passed → insufficient_context
```

Qdrant activates a new index only after the upload and count check. The same corpus and model identity reuse the active collection. Set the model revision when recording an evaluation, and reindex after changing embedding weights. The API checks that every quote appears in the chunk it cites. Answer completeness and whether the evidence supports every claim are measured separately, by the judge.

## Houdini

See [integrations/houdini](../integrations/houdini/README.md).

## Evaluation commands

See [evaluation.md](evaluation.md#reproducing-the-evaluation).
