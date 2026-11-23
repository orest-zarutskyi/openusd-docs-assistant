"""Local model and vector-store adapters for the application workflow."""

import hashlib
import json
from itertools import batched
from pathlib import Path
from typing import Literal
from uuid import uuid4

import httpx
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from ollama import ResponseError
from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from .chat import (
    MAX_OUTPUT_TOKENS,
    REASONING_MAX_TOKENS,
    SYSTEM_PROMPT,
    Usage,
    answer_schema,
    invalid_output,
    user_message,
)
from .models import Chunk, DependencyTimeout, DependencyUnavailable, DraftAnswer, InvalidModelOutput
from .retrieval import Mode, SearchResult


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENUSD_", env_file=".env", extra="ignore")

    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_path: Path | None = None
    ollama_url: str = "http://127.0.0.1:11434"
    chat_model: str = "qwen3:4b"
    embedding_model: str = "nomic-embed-text:v1.5"
    embedding_revision: str = ""
    top_k: int = Field(default=8, ge=1, le=10)
    # Defaults below were chosen on eval/questions.jsonl (dev) only; see
    # reports/retrieval_dev.md. Re-tune them on dev after changing models or chunking.
    retrieval_mode: Mode = "hybrid-rerank"
    reranker_model: str = "BAAI/bge-reranker-base"
    # Refusal gates: cosine for dense and hybrid, raw cross-encoder score for rerank.
    # The dev cosine cut was 0.6891 for dense and 0.6752 for hybrid; dense's is the default.
    min_score: float = Field(default=0.6891, ge=0, le=1)
    rerank_min_score: float = -0.9831
    # Candidates taken from each of BM25 and dense before fusion, and how many of the
    # fused list the cross-encoder rescores.
    candidate_depth: int = Field(default=50, ge=10, le=200)
    rerank_depth: int = Field(default=20, ge=5, le=100)
    reranker_cache: str = "data/fastembed"
    model_timeout: float = Field(default=60, gt=0, le=300)
    # Answer generation: Ollama (local) or the Gemini API. Embeddings always use Ollama,
    # so switching the chat model never changes what is retrieved.
    chat_provider: Literal["ollama", "gemini"] = "ollama"
    gemini_model: str = ""
    gemini_api_key: SecretStr | None = None  # read from .env only; never logged
    gemini_thinking_budget: int | None = None
    gemini_thinking_level: str | None = None
    # Qwen3-family "thinking", chosen per model on dev (reports/variants_dev.md):
    # qwen3:4b refused every dev question without it.
    ollama_reasoning: bool = True
    ollama_num_ctx: int = Field(default=16384, ge=4096, le=131072)
    # LLM judge for answer evaluation; must not be one of the compared models.
    judge_model: str = ""
    # gemini (the Gemini API key above) or openai-compatible (a /chat/completions gateway).
    judge_provider: Literal["gemini", "openai-compatible"] = "gemini"
    judge_base_url: str = ""
    judge_api_key: SecretStr | None = None  # read from .env only; never logged
    # The judge reasons over long contexts; 60 s ended in 504 DEADLINE_EXCEEDED on dev.
    judge_timeout: float = Field(default=180, gt=0, le=600)

    @field_validator(
        "gemini_api_key",
        "gemini_thinking_budget",
        "gemini_thinking_level",
        "judge_api_key",
        mode="before",
    )
    @classmethod
    def blank_is_unset(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class OllamaModels:
    def __init__(self, settings: Settings) -> None:
        client_kwargs = {"timeout": settings.model_timeout}
        self.embeddings = OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_url,
            client_kwargs=client_kwargs,
        )
        self.nomic_prefixes = settings.embedding_model.split(":")[0] == "nomic-embed-text"
        self.chat = ChatOllama(
            model=settings.chat_model,
            base_url=settings.ollama_url,
            temperature=0,
            reasoning=settings.ollama_reasoning,
            # Thinking tokens count against num_predict, so reasoning needs a larger budget.
            num_predict=REASONING_MAX_TOKENS if settings.ollama_reasoning else MAX_OUTPUT_TOKENS,
            # Ollama's default 4096-token window silently truncates long prompts and cuts
            # reasoning off before the JSON answer; 5 excerpts need far less than this.
            num_ctx=settings.ollama_num_ctx,
            client_kwargs=client_kwargs,
        ).with_structured_output(answer_schema(), method="json_schema", include_raw=True)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.nomic_prefixes:
            texts = [f"search_document: {text}" for text in texts]
        try:
            return self.embeddings.embed_documents(texts)
        except httpx.TimeoutException as exc:
            raise DependencyTimeout("The embedding model timed out.") from exc
        except (httpx.HTTPError, ResponseError, ConnectionError) as exc:
            raise DependencyUnavailable("The embedding model is unavailable.") from exc

    def embed_query(self, question: str) -> list[float]:
        if self.nomic_prefixes:
            question = f"search_query: {question}"
        try:
            return self.embeddings.embed_query(question)
        except httpx.TimeoutException as exc:
            raise DependencyTimeout("The embedding model timed out.") from exc
        except (httpx.HTTPError, ResponseError, ConnectionError) as exc:
            raise DependencyUnavailable("The embedding model is unavailable.") from exc

    def generate(self, question: str, context: list[Chunk]) -> DraftAnswer:
        return self.generate_with_usage(question, context)[0]

    def generate_with_usage(self, question: str, context: list[Chunk]) -> tuple[DraftAnswer, Usage]:
        try:
            result = self.chat.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_message(question, context)),
                ]
            )
            metadata = getattr(result["raw"], "usage_metadata", None) or {}
            usage = Usage(metadata.get("input_tokens", 0), metadata.get("output_tokens", 0))
            if result["parsing_error"] is not None or result["parsed"] is None:
                raise invalid_output(usage)
            try:
                return DraftAnswer.model_validate(result["parsed"]), usage
            except ValidationError as exc:
                raise invalid_output(usage) from exc
        except (ValidationError, OutputParserException) as exc:
            raise InvalidModelOutput("The model returned an invalid response.") from exc
        except httpx.TimeoutException as exc:
            raise DependencyTimeout("The chat model timed out.") from exc
        except (httpx.HTTPError, ResponseError, ConnectionError) as exc:
            raise DependencyUnavailable("The chat model is unavailable.") from exc


class QdrantIndex:
    def __init__(self, client: QdrantClient, embeddings: OllamaModels, settings: Settings):
        self.client = client
        self.embeddings = embeddings
        self.top_k = settings.top_k
        self.min_score = settings.min_score
        identity = f"{settings.embedding_model}\0{settings.embedding_revision}"
        self.alias = "openusd_" + hashlib.sha256(identity.encode()).hexdigest()[:16]

    def active_collection(self) -> str | None:
        aliases = self.client.get_aliases().aliases
        return next(
            (alias.collection_name for alias in aliases if alias.alias_name == self.alias), None
        )

    def ready(self) -> bool:
        try:
            return self.active_collection() is not None
        except (ResponseHandlingException, UnexpectedResponse):
            return False

    def index(self, chunks: list[Chunk]) -> bool:
        """Build a complete collection before changing the alias. Return whether it changed."""
        if not chunks:
            raise ValueError("The corpus produced no chunks.")
        payloads = [chunk.model_dump(mode="json") for chunk in chunks]
        snapshot = hashlib.sha256(json.dumps(payloads, sort_keys=True).encode()).hexdigest()[:20]
        prefix = f"{self.alias}_{snapshot}_"
        active = self.active_collection()
        if active and active.startswith(prefix):
            return False

        vectors = [
            vector
            for batch in batched(chunks, 16)
            for vector in self.embeddings.embed_documents([chunk.text for chunk in batch])
        ]
        if len(vectors) != len(chunks) or not all(vectors):
            raise DependencyUnavailable("The embedding model returned an incomplete batch.")
        size = len(vectors[0])
        if any(len(vector) != size for vector in vectors):
            raise DependencyUnavailable("The embedding model returned inconsistent dimensions.")

        staging = prefix + uuid4().hex[:12]
        self.client.create_collection(
            collection_name=staging,
            vectors_config=models.VectorParams(size=size, distance=models.Distance.COSINE),
        )
        for batch in batched(zip(chunks, payloads, vectors, strict=True), 64):
            self.client.upsert(
                collection_name=staging,
                points=[
                    models.PointStruct(id=chunk.id, payload=payload, vector=vector)
                    for chunk, payload, vector in batch
                ],
                wait=True,
            )
        if self.client.count(staging, exact=True).count != len(chunks):
            raise RuntimeError("Index point count differs from the corpus chunk count.")

        actions = []
        if self.active_collection():
            actions.append(
                models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=self.alias))
            )
        actions.append(
            models.CreateAliasOperation(
                create_alias=models.CreateAlias(collection_name=staging, alias_name=self.alias)
            )
        )
        self.client.update_collection_aliases(change_aliases_operations=actions)
        return True

    def retrieve(self, question: str) -> list[Chunk]:
        return self._query(question, self.top_k, self.min_score).chunks

    def search(self, question: str, limit: int) -> SearchResult:
        """Rank by cosine similarity without a threshold; the caller decides on refusal."""
        return self._query(question, limit, None)

    def _query(self, question: str, limit: int, threshold: float | None) -> SearchResult:
        try:
            collection = self.active_collection()
            if collection is None:
                raise DependencyUnavailable("Index the OpenUSD corpus before asking questions.")
            result = self.client.query_points(
                collection_name=collection,
                query=self.embeddings.embed_query(question),
                limit=limit,
                score_threshold=threshold,
                with_payload=True,
            )
            points = result.points
            return SearchResult(
                [Chunk.model_validate(point.payload) for point in points],
                [point.score for point in points],
                points[0].score if points else None,
            )
        except ResponseHandlingException as exc:
            if isinstance(exc.source, httpx.TimeoutException):
                raise DependencyTimeout("Qdrant timed out.") from exc
            raise DependencyUnavailable("Qdrant is unavailable.") from exc
        except (UnexpectedResponse, ValidationError, ValueError) as exc:
            raise DependencyUnavailable("The Qdrant index is unavailable or incompatible.") from exc


def connect_qdrant(settings: Settings) -> QdrantClient:
    if settings.qdrant_path is not None:
        return QdrantClient(path=str(settings.qdrant_path))
    return QdrantClient(url=settings.qdrant_url, timeout=10)
