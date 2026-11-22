from uuid import uuid4

import pytest
from qdrant_client import QdrantClient

from openusd_assistant.adapters import QdrantIndex, Settings
from openusd_assistant.models import Chunk, DependencyUnavailable


class StubEmbeddings:
    def __init__(self):
        self.document_calls = 0

    def embed_documents(self, texts):
        self.document_calls += 1
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, question):
        return [1.0, 0.0]


def make_chunk(text):
    return Chunk(
        id=str(uuid4()),
        path="docs/intro.rst",
        title="Layers",
        start_line=4,
        end_line=4,
        text=text,
        url="https://github.com/PixarAnimationStudios/OpenUSD/blob/example/docs/intro.rst#L4",
    )


def test_identical_index_is_reused_and_changed_corpus_replaces_results():
    with_qdrant = QdrantClient(":memory:")
    try:
        embeddings = StubEmbeddings()
        index = QdrantIndex(with_qdrant, embeddings, Settings(_env_file=None))
        assert not index.ready()
        with pytest.raises(DependencyUnavailable):
            index.retrieve("What is a layer?")
        first_chunk = make_chunk("A first layer.")
        assert index.index([first_chunk])
        assert index.ready()
        assert not index.index([first_chunk])
        assert embeddings.document_calls == 1
        assert index.retrieve("What is a layer?") == [first_chunk]

        changed_chunk = make_chunk("An updated layer.")
        assert index.index([changed_chunk])
        assert index.retrieve("What is a layer?") == [changed_chunk]
        assert with_qdrant.count(index.active_collection(), exact=True).count == 1
    finally:
        with_qdrant.close()


class DirectionalEmbeddings(StubEmbeddings):
    vectors = {"near": [1.0, 0.0], "mid": [0.6, 0.8], "far": [0.0, 1.0]}

    def embed_documents(self, texts):
        return [self.vectors[text] for text in texts]


def test_search_ranks_by_cosine_without_threshold_and_retrieve_applies_it():
    client = QdrantClient(":memory:")
    try:
        settings = Settings(_env_file=None, top_k=3, min_score=0.5)
        index = QdrantIndex(client, DirectionalEmbeddings(), settings)
        chunks = [make_chunk(text) for text in ("far", "near", "mid")]
        index.index(chunks)

        result = index.search("query", 3)
        assert [chunk.text for chunk in result.chunks] == ["near", "mid", "far"]
        assert result.scores == pytest.approx([1.0, 0.6, 0.0], abs=1e-6)
        assert result.confidence == pytest.approx(1.0)
        assert [chunk.text for chunk in index.retrieve("query")] == ["near", "mid"]
    finally:
        client.close()
