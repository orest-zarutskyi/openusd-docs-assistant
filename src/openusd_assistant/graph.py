from collections.abc import Callable
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from .models import AskResponse, Chunk, DraftAnswer, InvalidModelOutput, Source
from .quotes import CitationCheck, match_quote

Retriever = Callable[[str], list[Chunk]]
Generator = Callable[[str, list[Chunk]], DraftAnswer]


class QueryState(TypedDict):
    question: str
    context: NotRequired[list[Chunk]]
    draft: NotRequired[DraftAnswer]
    result: NotRequired[AskResponse]


def _refuse() -> AskResponse:
    return AskResponse(
        status="insufficient_context",
        answer=(
            "The retrieved OpenUSD documentation does not provide enough information "
            "to answer this question."
        ),
    )


def _verified_answer(
    draft: DraftAnswer, context: list[Chunk], check: CitationCheck = "strict"
) -> AskResponse:
    if draft.status == "insufficient_context":
        return _refuse()

    if not draft.answer or not draft.evidence:
        raise InvalidModelOutput()

    chunks = {chunk.id: chunk for chunk in context}
    sources = []
    for evidence in draft.evidence:
        chunk = chunks.get(evidence.chunk_id)
        # Markup-insensitive but word-exact: see quotes.match_quote and ADR 16.
        shown = match_quote(evidence.quote, chunk.text, check) if chunk else None
        if shown is None and check != "strict":
            # The quote may be in another retrieved chunk than the one the model named.
            for other in context:
                shown = match_quote(evidence.quote, other.text, check)
                if shown is not None:
                    chunk = other
                    break
        if shown is None:
            raise InvalidModelOutput()

        sources.append(
            Source(
                chunk_id=chunk.id,
                path=chunk.path,
                title=chunk.title,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                url=chunk.url,
                quote=shown,
            )
        )

    return AskResponse(status="answer", answer=draft.answer, sources=sources)


def build_graph(retrieve: Retriever, generate: Generator, check: CitationCheck = "strict"):
    def retrieve_context(state: QueryState) -> dict:
        return {"context": retrieve(state["question"])}

    def after_retrieval(state: QueryState) -> str:
        return "generate" if state["context"] else "refuse"

    def refuse(state: QueryState) -> dict:
        return {"result": _refuse()}

    def generate_answer(state: QueryState) -> dict:
        try:
            draft = DraftAnswer.model_validate(generate(state["question"], state["context"]))
        except ValidationError as exc:
            raise InvalidModelOutput() from exc
        return {"draft": draft}

    def verify_answer(state: QueryState) -> dict:
        return {"result": _verified_answer(state["draft"], state["context"], check)}

    graph = StateGraph(QueryState)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("generate", generate_answer)
    graph.add_node("verify", verify_answer)
    graph.add_node("refuse", refuse)
    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges(
        "retrieve", after_retrieval, {"generate": "generate", "refuse": "refuse"}
    )
    graph.add_edge("generate", "verify")
    graph.add_edge("verify", END)
    graph.add_edge("refuse", END)
    return graph.compile()
