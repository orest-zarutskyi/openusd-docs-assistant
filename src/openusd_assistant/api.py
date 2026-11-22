from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .graph import Generator, Retriever, build_graph
from .models import AskRequest, AskResponse, AssistantError, DependencyUnavailable


def create_app(retrieve: Retriever, generate: Generator, ready: Callable[[], bool]) -> FastAPI:
    graph = build_graph(retrieve, generate)
    app = FastAPI(title="OpenUSD Docs Assistant", version="0.1.0")

    @app.exception_handler(AssistantError)
    async def assistant_error(_request: Request, exc: AssistantError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readiness() -> dict[str, str]:
        if not ready():
            raise DependencyUnavailable()
        return {"status": "ready"}

    @app.post("/ask", response_model=AskResponse)
    def ask(payload: AskRequest) -> AskResponse:
        return graph.invoke({"question": payload.question})["result"]

    return app
