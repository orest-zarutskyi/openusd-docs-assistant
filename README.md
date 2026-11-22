# OpenUSD Docs Assistant

A local question-answering service for OpenUSD scene composition. It finds relevant passages in a fixed set of upstream docs and cites the exact source lines. If the retrieved text is insufficient, it returns a clear refusal. The service runs independently of Houdini.

## Development plan

1. **Corpus and examples.** Pin the text documentation from OpenUSD 26.08, retain license notices and exact line references, and write the first ten evaluation questions with expected passages or refusals.
2. **Working local API.** Index documents in Qdrant. Use a small LangGraph workflow for retrieval, generation and citation validation. Run inference through a configurable local model and expose the workflow through FastAPI. A repeated index build should not duplicate points.
3. **Evaluation and tests.** Expand to 25–30 questions. Compare dense retrieval to a lexical baseline, then measure whether answers are supported by sources and whether the system refuses appropriately. Keep a held-out set and report counts, failure cases and model configuration.
4. **Reproduction and demo.** Document setup, provide Docker Compose and CI checks, and record a short demo showing an answer, its source and a refusal.

The first public release covers English questions on stages, layers, references, payloads and variants. A Houdini integration, one render-log diagnosis scenario and hosted deployment are later options.

## Source material

The corpus is selected text documentation from [OpenUSD 26.08](https://github.com/PixarAnimationStudios/OpenUSD/releases/tag/v26.08). See the upstream [license](https://github.com/PixarAnimationStudios/OpenUSD/blob/ee47c679abde5b467a7b6a41f3b2285564a4222e/LICENSE.txt). Local data and indexes are reproducible outputs and are ignored by Git.

## Local setup

Use Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Run the commands from the project root.

```powershell
uv sync --locked --extra dev
uv run --locked openusd-assistant check-corpus
uv run --locked openusd-assistant eval-retrieval --backend bm25
uv run --locked --extra dev pytest
```

For an existing snapshot, pass `--source-dir data/openusd-26.08` to `check-corpus`, `index` or the BM25 evaluation. The directory should contain the five files listed in the manifest under `docs/`, plus the original `LICENSE.txt` and `NOTICE.txt`.

For live generation, start [Ollama](https://ollama.com/) on the host, pull the two models below, and select the Qdrant storage. For a single local process without Docker, set `OPENUSD_QDRANT_PATH` to `data/qdrant` in `.env`. Run the indexer before starting the API because Qdrant's embedded storage accepts a single process at a time.

```powershell
ollama pull qwen3:4b
ollama pull nomic-embed-text:v1.5
uv run --locked openusd-assistant index
uv run --locked openusd-assistant serve
```

Open the generated API interface at [localhost:8000/docs](http://127.0.0.1:8000/docs). Try “Which composition arc lets me open a stage before loading a heavy asset?” and “What Pyro settings should I use for my smoke shot?” The first question is covered by the corpus. The second is a refusal case.

### Docker Compose

With Docker Desktop and host Ollama running, build and start the services, then index the corpus. The API is available on loopback only. For other host layouts, set `OPENUSD_OLLAMA_URL` to the host model service address reachable from the API container.

```powershell
docker compose up -d --build
docker compose run --rm api index
```

### Workflow

```text
Pinned docs → verify SHA-256 → split by source lines → index in Qdrant
Question → FastAPI → LangGraph retrieve → generate → verify quotes → answer
                                   ↘ empty context → insufficient_context
```

Qdrant activates a new index only after the upload and count check. The same corpus and model identity reuse the active collection. Set the model revision when recording an evaluation, and reindex after changing embedding weights. The API checks that excerpts came from retrieved chunks. Answer correctness and whether the evidence supports every claim are measured separately.

### First retrieval baseline

The development set contains eight answerable questions and two refusal cases. On the 41 chunks from the pinned snapshot, SQLite BM25 found the expected source in the first five results for **7 of 8** answerable questions, with MRR@5 **0.67**. The stage-creation question missed its expected paragraph. This is a small development baseline. Dense retrieval, live answer quality, refusal quality and the Docker build still need their own runs.
